import asyncio
import logging
import re
from typing import Optional

import aiohttp
from mcstatus import JavaServer
from mcstatus.responses import JavaStatusResponse

from models import ServerInfo
from settings import settings

logger = logging.getLogger(__name__)


async def get_location(ip: str) -> str:
    url = f"http://ipwho.is/{ip}?lang=ru"
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
            status = await asyncio.wait_for(server.async_status(), timeout=settings.timeout)
            ping = server.ping()
            names = [p.name for p in (status.players.sample or [])]
            motd = status.motd.to_plain()
            map_name = (
                motd.replace("Hosted by StickyPiston.co", "")
               .split("by")[0].strip().lower().replace(" ", ""))
            map_name = re.sub(r'[^a-zA-Z0-9]', '', map_name)
            map_link = f"https://trial.stickypiston.co/map/{map_name}"

            return ServerInfo(
                ip=ip,
                port=port,
                version=status.version.name,
                motd=motd,
                online=status.players.online,
                max=status.players.max,
                players=names,
                location=location,
                ping=int(ping),
                icon=status.icon,
                map_link=map_link
            )
        except asyncio.TimeoutError:
            logger.info(f"[!] {ip}:{port} — не отвечает")
            return None
        except Exception as e:
            logger.error(f"{ip}:{port} - ошибка: {e}")
            return None


async def scan_ips(ips: list[str]) -> list[ServerInfo]:
    sem = asyncio.Semaphore(settings.concurrency_limit)
    tasks = []
    for ip in ips:
        location = await get_location(ip)
        print(f"🔍 Сканирование {ip} ({location}) порты {settings.port_start}–{settings.port_end}")
        tasks.extend([
            mc_ping(ip, port, sem, location)
            for port in range(settings.port_start, settings.port_end + 1)
        ])

    results = await asyncio.gather(*tasks)
    found = [r for r in results if r is not None]
    return found
