import asyncio
import json
import logging
import re
import struct
from urllib.request import Request, urlopen

import aiohttp
from typing_extensions import TypedDict

import config
from config import PORT_START, PORT_END, CONCURRENCY_LIMIT

logger = logging.getLogger(__name__)

COLOR_CODES = {
    '0': '\033[30m',  # чёрный
    '1': '\033[34m',  # тёмно-синий
    '2': '\033[32m',  # тёмно-зелёный
    '3': '\033[36m',  # тёмно-бирюзовый
    '4': '\033[31m',  # тёмно-красный
    '5': '\033[35m',  # фиолетовый
    '6': '\033[33m',  # оранжевый/золотой
    '7': '\033[37m',  # светло-серый
    '8': '\033[90m',  # тёмно-серый
    '9': '\033[94m',  # синий
    'a': '\033[92m',  # зелёный
    'b': '\033[96m',  # бирюзовый
    'c': '\033[91m',  # красный
    'd': '\033[95m',  # розовый
    'e': '\033[93m',  # жёлтый
    'f': '\033[97m',  # белый
    'r': '\033[0m',  # сброс
    'l': '',  # жирный (можно добавить \033[1m)
    'n': '',  # подчёркнутый (можно \033[4m)
    'o': '',  # курсив (можно \033[3m)
    'm': '',  # зачёркнутый (можно \033[9m)
}


class ServerInfo(TypedDict):
    ip: str
    port: int
    version: str
    motd: str
    online: str
    max: str
    players: list[str]
    country: str
    icon: str


def strip_ansi(text: str) -> str:
    ansi_escape = re.compile(r'\x1B\[[0-?]*[ -/]*[@-~]')
    return ansi_escape.sub('', text)


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


def encode_varint(value: int) -> bytes:
    result = b''
    while True:
        byte = value & 0x7F
        value >>= 7
        result += struct.pack('B', byte | (0x80 if value > 0 else 0))
        if not value:
            break
    return result


async def read_varint(reader: asyncio.StreamReader) -> int:
    num_read = 0
    result = 0
    while True:
        byte = await reader.read(1)
        if not byte:
            raise IOError("Сервер закрыл соединение")
        byte = byte[0]
        result |= (byte & 0x7F) << (7 * num_read)
        num_read += 1
        if not (byte & 0x80):
            break
    return result


def extract_text(description) -> str:
    if isinstance(description, str):
        return description
    elif isinstance(description, dict):
        if 'text' in description:
            return description['text']
        elif 'extra' in description:
            return ''.join(part.get('text', '') for part in description['extra'])
    return str(description)


def parse_motd_colors(text: str) -> str:
    result = ''
    i = 0
    while i < len(text):
        if text[i] == '§' and i + 1 < len(text):
            code = text[i + 1].lower()
            result += COLOR_CODES.get(code, '')
            i += 2
        else:
            result += text[i]
            i += 1
    return result + '\033[0m'  # сброс цвета в конце


async def mc_ping(ip: str, port: int, sem: asyncio.Semaphore, location: str) -> ServerInfo:
    async with sem:
        for protocol_version in config.PROTOCOLS:
            try:
                reader, writer = await asyncio.wait_for(
                    asyncio.open_connection(ip, port), timeout=config.TIMEOUT
                )

                host = ip.encode('utf-8')
                handshake_data = (
                        encode_varint(protocol_version) +
                        encode_varint(len(host)) + host +
                        struct.pack('>H', port) +
                        encode_varint(1)
                )
                handshake_packet = encode_varint(0) + handshake_data
                writer.write(encode_varint(len(handshake_packet)) + handshake_packet)

                writer.write(b'\x01\x00')
                await writer.drain()

                _ = await read_varint(reader)
                _ = await read_varint(reader)
                json_length = await read_varint(reader)
                data = await reader.readexactly(json_length)

                writer.close()
                await writer.wait_closed()

                status = json.loads(data.decode('utf-8'))

                version = status.get("version", {}).get("name", "?")
                players = status.get("players",{})
                motd_raw = status.get("description",{})
                motd = extract_text(motd_raw)
                motd = parse_motd_colors(motd)
                motd = motd.replace("Hosted by trial.StickyPiston.co", "")
                sample = players.get("sample", [])
                names = [p.get("name", "") for p in sample]

                return ServerInfo(
                    ip=ip, port=port, country=location,
                    version=version, motd=motd,
                    online=players.get("online", 0),
                    max=players.get("max",0),
                    players=names,
                    icon=status.get("favicon")
                )
            except Exception:
                continue  # пробуем следующий протокол

        with open("scan_errors.log", "a") as f:
            f.write(f"[{ip}:{port}] No compatible protocol found\n")


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
