import asyncio

from settings import settings
from utils import scan_ips
from models import ServerInfo

servers = []

def print_server_info(info: ServerInfo):
    print(f"🟢 {info.ip}:{info.port} — сервер найден!")
    print(f"   ➤ Версия: {info.version}")
    print(f"   ➤ MOTD: {info.motd}")
    print(f"   ➤ Онлайн: {info.online} / {info.max}")

    if info.players:
        print("   ➤ Игроки онлайн:")
        for player in info.players:
            print(f"      • {player}")


async def main():
    for i, ip in enumerate(settings.target_ips, 1):
        print(f"\n[{i}/{len(settings.target_ips)}] ", end="")
        new_servers = await scan_ips([ip])
        servers.extend(new_servers)
        for new_server in new_servers:
            print_server_info(new_server)
    print("\n🔚 Сканирование завершено.")


if __name__ == "__main__":
    asyncio.run(main())
    input()