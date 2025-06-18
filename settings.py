from pydantic import BaseModel, Field
from typing import List
import json
import os

SETTINGS_PATH = "settings.json"


class Settings(BaseModel):
    target_ips: List[str] = Field(default_factory=lambda: [
        "51.75.167.121", "148.251.56.99", "135.181.49.9",
        "88.198.26.90", "51.161.201.179", "139.99.71.89",
        "135.148.104.247", "51.81.251.246"
    ])
    port_start: int = 25565
    port_end: int = 25665
    timeout: float = 2.5
    concurrency_limit: int = 1000

    @classmethod
    def load(cls) -> "Settings":
        if os.path.exists(SETTINGS_PATH):
            with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                return cls(**data)
        else:
            default = cls()
            default.save()
            return default

    def save(self):
        with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
            json.dump(self.model_dump(), f, indent=4)


settings = Settings.load()
