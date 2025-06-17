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

async function load() {
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
    td.colSpan = 7;
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
    const icon = s.icon ? `<img src=${s.icon} alt="server icon"/>` : "Нет иконки";
    tr.innerHTML = `
      <td>${i+1}</td>
      <td>${s.ip}:${s.port}</td>
      <td>${s.version}</td>
      <td>${icon}</td>
      <td>${s.motd.replace('\n', '</br>')}</td>
      <td>${s.online}/${s.max}</td>
      <td>${s.players.join(', ')}</td>
      <td>${s.country}</td>
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
    const vals = [a.ip + ':' + a.port, a.version, a.motd, a.online + '/' + a.max, a.players, a.country];
    let x = (col === 1) ? a.ip + ':' + a.port : Object.values(a)[col];
    let y = (col === 1) ? b.ip + ':' + b.port : Object.values(b)[col];

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
window.onload = load;