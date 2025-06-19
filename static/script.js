let data = [], dir = {};

function showLoading() {
  const tbody = document.querySelector('#servers tbody');
  tbody.innerHTML = '';

  const tr = document.createElement('tr');
  const td = document.createElement('td');
  td.colSpan = 8;
  td.style.textAlign = 'center';

  const loaderContainer = document.createElement('div');
  loaderContainer.className = 'loader-container';

  const spinner = document.createElement('div');
  spinner.className = 'loader-spinner';

  const text = document.createElement('span');
  text.className = 'loader-text';
  text.textContent = 'Загрузка…';

  loaderContainer.appendChild(spinner);
  loaderContainer.appendChild(text);
  td.appendChild(loaderContainer);
  tr.appendChild(td);
  tbody.appendChild(tr);
}

async function loadServers() {
  // пока грузим — показываем loading и блокируем кнопку
  showLoading();
  document.querySelector('button').disabled = true;

  try {
    const res = await fetch('/servers');
    if (!res.ok) throw new Error('Ошибка загрузки данных');
    const json = await res.json();
    data = json.servers;
    render(data);
  } catch (e) {
    // на ошибку тоже выводим её в качестве одной строки
    const tbody = document.querySelector('#servers tbody');
    tbody.innerHTML = '';
    const tr = document.createElement('tr');
    const td = document.createElement('td');
    td.colSpan = 8;
    td.style.textAlign = 'center';
    td.style.color = 'red';
    td.textContent = 'Ошибка: ' + e.message;
    tr.appendChild(td);
    tbody.appendChild(tr);
  } finally {
    document.querySelector('button').disabled = false;
  }
}

function render(arr) {
  const tbody = document.querySelector('#servers tbody');
  tbody.innerHTML = '';
  arr.forEach((s, i) => {
    const tr = document.createElement('tr');
    const icon_url = s.icon ? s.icon : "/static/default_icon.png" ;

    tr.innerHTML = `
      <td>${i+1}</td>
      <td class="info-cell">
        ${s.ip}:${s.port}</br>
        ${s.location}</br>
        ping: ${s.ping} ms</br>
      </td>
      <td>${s.version}</td>
      <td class="icon-motd">
        <img src="${icon_url}" alt="server icon" />
        <div class="motd">
            ${s.motd.replace('\n', '<br>')}</br>
            <a href='${s.map_link}'>Возможная ссылка на карту</a>
        </div>
      </td>
      <td>${s.online}/${s.max}<br/>${s.players.join(', ')}</td>
    `;
    tbody.appendChild(tr);
  });
  filter();    // применить текущий фильтр
  // clearSort(); // сбросить стрелки
}

function filter() {
  const q = document.getElementById('search').value.trim().toLowerCase();
  document.querySelectorAll('#servers tbody tr').forEach(tr => {
    tr.style.display = tr.textContent.toLowerCase().includes(q) ? '' : 'none';
  });
}

function clearSort() {
  document.querySelectorAll('th.sortable').forEach(th => {
    th.classList.remove('asc', 'desc');
  });
}

function sort(col) {
  const ths = document.querySelectorAll('th.sortable');
  const wasAsc = ths[col].classList.contains('asc');
  // меняем направление
  dir[col] = wasAsc ? 'desc' : 'asc';
  // сбрасываем все
  clearSort();
  ths[col].classList.add(dir[col]);

  const numeric = false;
  data.sort((a, b) => {
    const vals = ['ping', 'version', 'motd', 'online', 'location'];
    let x = a[vals[col]];
    let y = b[vals[col]];

    if (numeric) {
      const xn = parseFloat(x), yn = parseFloat(y);
      return dir[col] === 'asc' ? xn - yn : yn - xn;
    } else {
        if (x < y) return dir[col] === 'asc' ? -1 : 1;
        if (x > y) return dir[col] === 'asc' ? 1 : -1;
        return 0;
    }
  });
  render(data);
}

// грузим сразу при старте
// window.onload = loadServers;

let settings = {};
async function fetchSettings() {
    const res = await fetch("/settings");
    settings = await res.json();
}

const ipTagsContainer = document.getElementById('ip-tags-container');

async function renderSettings() {
    const form = document.getElementById("settings-form");
    try {
      ipSet.clear();
      ipTagsContainer.innerHTML = "";
      console.log(settings.target_ips)
      settings.target_ips.forEach(ip => addIP(ip));

      form.port_start.value = settings.port_start;
      form.port_end.value = settings.port_end;
      form.timeout.value = settings.timeout;
      form.concurrency_limit.value = settings.concurrency_limit;
    } catch (e) {
      console.error("Ошибка загрузки настроек", e);
      showToast("Ошибка загрузки настроек")
    }
  }

async function showSettings() {
    const settingsDialog = document.getElementById("settings-modal");
    settingsDialog.showModal();
    await fetchSettings();
    renderSettings();

}

function closeSettings() {
    const settingsDialog = document.getElementById("settings-modal");
    settingsDialog.close()
}

 async function submitSettings(e) {
    if (e) e.preventDefault();
    const form = document.getElementById("settings-form");

    const body = {
      target_ips: getIPsFromTags(),
      port_start: parseInt(form.port_start.value),
      port_end: parseInt(form.port_end.value),
      timeout: parseFloat(form.timeout.value),
      concurrency_limit: parseInt(form.concurrency_limit.value)
    };

    try {
      await fetch("/settings", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify(body)
      });
      showToast("Настройки сохранены!");
    } catch (e) {
      showToast("Ошибка при сохранении настроек");
      console.error(e);
    }
 }

function showToast(message, duration = 3000) {
  const container = document.getElementById("toast-container");

  const toast = document.createElement("div");
  toast.className = "toast show";
  toast.textContent = message;

  container.appendChild(toast);

  setTimeout(() => {
    toast.classList.remove("show");
    toast.addEventListener("transitionend", () => toast.remove());
  }, duration);
}
const ipInput = document.getElementById('ip-input');
const addIpBtn = document.getElementById('add-ip-btn');

const ipSet = new Set();

function isValidIP(ip) {
  // Простая проверка IPv4, без поддержки IPv6
  const parts = ip.trim().split('.');
  if (parts.length !== 4) return false;
  return parts.every(part => {
    const n = Number(part);
    return !isNaN(n) && n >= 0 && n <= 255 && part === n.toString();
  });
}

function createTag(ip) {
  const tag = document.createElement('span');
  tag.className = 'tag';
  tag.textContent = ip;

  const removeBtn = document.createElement('span');
  removeBtn.className = 'remove-tag';
  removeBtn.textContent = '×';
  removeBtn.onclick = () => {
    ipTagsContainer.removeChild(tag);
    ipSet.delete(ip);
  };

  tag.appendChild(removeBtn);
  return tag;
}

const errorEl = document.getElementById('ip-error');

function showError(message) {
  errorEl.textContent = message;
  errorEl.classList.add('show');
}

function hideError() {
  errorEl.textContent = '';
  errorEl.classList.remove('show');
}

function addIP(ip) {
  if (!isValidIP(ip)) {
    showError('Неправильный формат IP!');
    return;
  }
  if (ipSet.has(ip)) {
    showError('Этот IP уже добавлен');
    return;
  }

  // Всё хорошо — скрываем ошибку
  hideError();

  const tag = createTag(ip);
  ipTagsContainer.appendChild(tag);
  ipSet.add(ip);
  ipInput.value = '';
}

addIpBtn.addEventListener('click', e => addIP(ipInput.value.trim()));

ipInput.addEventListener('keydown', e => {
  if (e.key === 'Enter') {
    e.preventDefault();
    addIP(ipInput.value.trim());
  }
});

function getIPsFromTags() {
  return Array.from(ipSet);
}

const toggleBtn = document.getElementById('theme-toggle');
const themes = ['light', 'dark', 'minecraft', 'vulkan'];

function getNextTheme(current) {
  const index = themes.indexOf(current);
  return themes[(index + 1) % themes.length];
}

function applyTheme(theme) {
  if (theme === 'light') {
    document.documentElement.removeAttribute('data-theme');
    localStorage.removeItem('theme');
  } else {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);
  }
}

// При загрузке страницы применяем сохранённую тему
const savedTheme = localStorage.getItem('theme') || 'light';
applyTheme(savedTheme);

// При клике – переключаем на следующую тему
toggleBtn.addEventListener('click', () => {
  const current = localStorage.getItem('theme') || 'light';
  const next = getNextTheme(current);
  applyTheme(next);
  showToast(`Выбрана тема ${next}`);
});