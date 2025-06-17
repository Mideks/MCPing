import asyncio
import logging
from typing import Optional

import aiohttp
from mcstatus import JavaServer
from mcstatus.responses import JavaStatusResponse
from typing_extensions import TypedDict

from config import PORT_START, PORT_END, CONCURRENCY_LIMIT
from config import TIMEOUT

logger = logging.getLogger(__name__)


class ServerInfo(TypedDict):
    ip: str
    port: int
    version: str
    motd: str
    online: int
    max: int
    players: list[str]
    country: str
    icon: str


async def get_location(ip: str) -> str:
    url = f"http://ipwho.is/{ip}"
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=5)) as response:
                if response.status != 200:
                    logger.info(f"[!] HTTP {response.status} для IP {ip}")
                    return "неизвестно"

                data = await response.json()

                if data.get("success") is True:
                    country = data.get("country", "неизвестно")
                    city = data.get("city", "")
                    return f"{country}{' / ' + city if city else ''}"
                else:
                    logger.info(f"[!] Ошибка API для IP {ip}: {data.get('message')}")
    except asyncio.TimeoutError:
        logger.info(f"[!] Таймаут при запросе {ip}")
    except Exception as e:
        logger.error(f"[!] Ошибка при запросе геолокации {ip}: {e}")

    return "неизвестно"


async def mc_ping(ip: str, port: int, sem: asyncio.Semaphore, location: str) -> Optional[ServerInfo]:
    async with sem:
        try:
            server = JavaServer(ip, port)
            status: JavaStatusResponse = await asyncio.wait_for(server.async_status(), timeout=TIMEOUT)
            names = [p.name for p in (status.players.sample or [])]

            return ServerInfo(
                ip=ip,
                port=port,
                version=status.version.name,
                motd=status.motd.to_plain(),
                online=status.players.online,
                max=status.players.max,
                players=names,
                country=location,
                icon=status.icon
            )
        except asyncio.TimeoutError:
            logger.info(f"[!] {ip}:{port} — не отвечает")
            return None


async def scan_ip(ip: str) -> list[ServerInfo]:
    location = await get_location(ip)
    print(f"🔍 Сканирование {ip} ({location}) порты {PORT_START}–{PORT_END}")
    sem = asyncio.Semaphore(CONCURRENCY_LIMIT)
    tasks = [
        mc_ping(ip, port, sem, location)
        for port in range(PORT_START, PORT_END + 1)
    ]
    results = await asyncio.gather(*tasks)
    found = [r for r in results if r is not None]
    return found
