from dataclasses import dataclass
from typing import Optional


@dataclass
class ServerInfo():
    ip: str
    port: int
    version: str
    motd: str
    online: int
    max: int
    players: list[str]
    location: str
    icon: Optional[str]
