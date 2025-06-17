import asyncio

from config import TARGET_IPS
from utils import ServerInfo, \
    scan_ip, parse_motd_colors

servers = []

def export_to_html(servers: list[dict], filename: str = "servers.html") -> None:
    with open(filename, "w", encoding="utf-8") as f:
        f.write("""<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <title>Minecraft Серверы</title>
    <style>
        body {
            font-family: sans-serif;
            background-color: #f8f9fa;
            padding: 40px;
        }
        h1 {
            text-align: center;
            color: #333;
        }
        #search {
            margin-bottom: 20px;
            padding: 10px;
            width: 100%;
            max-width: 400px;
            font-size: 16px;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            background: white;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        th, td {
            padding: 12px 16px;
            border: 1px solid #dee2e6;
            text-align: left;
        }
        th {
            background-color: #007bff;
            color: white;
            cursor: pointer;
        }
        tr:nth-child(even) {
            background-color: #f2f2f2;
        }
        td.motd {
            white-space: pre-wrap;
        }
        .hidden {
            display: none;
        }
        th.sortable {
        position: relative;
        padding-right: 30px;
        }
        th.sortable::after {
            content: '';
            position: absolute;
            right: 10px;
            top: 50%;
            transform: translateY(-50%);
            border: 6px solid transparent;
        }
        th.sortable.asc::after {
            border-bottom-color: white;
        }
        th.sortable.desc::after {
            border-top-color: white;
        }
                .search-container {
    text-align: center;
    margin-bottom: 20px;
}

    #search {
        width: 50%;
        max-width: 400px;
        padding: 10px 15px;
        font-size: 16px;
        border: 2px solid #666;
        border-radius: 25px;
        background-color: rgba(255, 255, 255, 0.8);
        transition: box-shadow 0.3s ease, background-color 0.3s ease;
        outline: none;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.15);
    }

    #search:focus {
        box-shadow: 0 0 8px #4a90e2;
        background-color: #fff;
        border-color: #4a90e2;
    }
    </style>
</head>
<body>
<h1>Список Minecraft-серверов</h1>
<div class="search-container">
    <input type="text" id="search" placeholder="🔍 Поиск по таблице...">
</div>

<table id="servers">
    <thead>
    <tr>
        <th class="sortable" onclick="sortTable(0)">#</th>
        <th class="sortable" onclick="sortTable(1)">Адрес</th>
        <th class="sortable" onclick="sortTable(2)">Версия</th>
        <th class="sortable" onclick="sortTable(3)">MOTD</th>
        <th class="sortable" onclick="sortTable(4)">Онлайн</th>
        <th class="sortable" onclick="sortTable(5)">Игроки</th>
        <th class="sortable" onclick="sortTable(6)">Страна</th>
    </tr>
    </thead>
    <tbody>
""")

        for i, srv in enumerate(servers):
            f.write(f"""    <tr>
        <td>{i}</td>
        <td>{srv['ip']}:{srv['port']}</td>
        <td>{srv['version']}</td>
        <td class="motd">{srv['motd']}</td>
        <td>{srv['online']}/{srv['max']}</td>
        <td>{srv['players']}</td>
        <td>{srv['country']}</td>
    </tr>
""")

        # JS: фильтр и сортировка
        f.write("""    </tbody>
</table>

<script>
document.getElementById('search').addEventListener('input', function () {
    const filter = this.value.trim().toLowerCase();
    const rows = document.querySelectorAll('#servers tbody tr');

    rows.forEach(row => {
        const text = row.textContent.toLowerCase();
        row.style.display = text.includes(filter) ? '' : 'none';
    });
});

function sortTable(n) {
    const table = document.getElementById("servers");
    const tbody = table.tBodies[0];
    const rows = Array.from(tbody.rows);
    const ths = table.tHead.rows[0].cells;

    let current = ths[n];
    let direction = "asc";

    // Проверим, что было ДО удаления классов
    const wasAsc = current.classList.contains("asc");
    const wasDesc = current.classList.contains("desc");

    // Сброс всех стрелочек
    for (let i = 0; i < ths.length; i++) {
        ths[i].classList.remove("asc", "desc");
    }

    // Переключение направления
    if (wasAsc) {
        direction = "desc";
    } else {
        direction = "asc";
    }
    current.classList.add(direction);

    const sorted = rows.sort((a, b) => {
        let x = a.cells[n].textContent.trim();
        let y = b.cells[n].textContent.trim();

        let xNum = parseFloat(x.replace(",", "."));
        let yNum = parseFloat(y.replace(",", "."));

        const isNumeric = !isNaN(xNum) && !isNaN(yNum);

        if (isNumeric) {
            return direction === "asc" ? xNum - yNum : yNum - xNum;
        } else {
            return direction === "asc"
                ? x.localeCompare(y, 'ru', { sensitivity: 'base' })
                : y.localeCompare(x, 'ru', { sensitivity: 'base' });
        }
    });

    sorted.forEach(row => tbody.appendChild(row));
}
</script>

</body>
</html>
""")


def print_server_info(info: ServerInfo):
    print(f"🟢 {info['ip']}:{info['port']} — сервер найден!")
    print(f"   ➤ Версия: {info['version']}")
    print(f"   ➤ MOTD: {parse_motd_colors(info['motd'])}")
    print(f"   ➤ Онлайн: {info['online']} / {info['max']}")

    if info["players"]:
        print("   ➤ Игроки онлайн:")
        for player in info["players"]:
            print(f"      • {player}")


async def main():
    for i, ip in enumerate(TARGET_IPS, 1):
        print(f"\n[{i}/{len(TARGET_IPS)}] ", end="")
        new_servers = await scan_ip(ip)
        servers.extend(new_servers)
        for new_server in new_servers:
            print_server_info(new_server)
    print("\n🔚 Сканирование завершено.")
    export_to_html(servers)


if __name__ == "__main__":
    asyncio.run(main())
    input()