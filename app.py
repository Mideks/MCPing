import os
import sys
import threading
from dataclasses import dataclass

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from config import TARGET_IPS
from utils import scan_ips
from models import ServerInfo

app = FastAPI()


if getattr(sys, 'frozen', False):  # Если упаковано в .exe
    # временная папка, куда PyInstaller распаковывает ресурсы
    base_dir = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
else:
    base_dir = os.path.dirname(os.path.abspath(__file__))

templates = Jinja2Templates(directory=os.path.join(base_dir, "templates"))
app.mount("/static", StaticFiles(directory=os.path.join(base_dir, "static")), name="static")

@dataclass
class Settings():
    target_ips: list[str]
    port_start: int
    port_end: int
    timeout: float
    concurrency_limit: int


settings_data = Settings(
    target_ips=[
        "51.75.167.121", "148.251.56.99", "135.181.49.9",
        "88.198.26.90", "51.161.201.179", "139.99.71.89",
        "135.148.104.247", "51.81.251.246"
    ],
    port_start=25565,
    port_end=25665,
    timeout=0.5,
    concurrency_limit=1000
)

@app.get("/settings")
def get_settings():
    return settings_data

@app.post("/settings")
def update_settings(new_settings: Settings):
    global settings_data
    settings_data = new_settings
    return {"status": "ok"}


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/servers")
async def api_servers():
    servers: list[ServerInfo] = []
    results = await scan_ips(TARGET_IPS)
    servers.extend(results)
    return {"servers": servers}


def open_browser():
    import webbrowser
    webbrowser.open("http://127.0.0.1:8000")

if __name__ == "__main__":
    # Авто‑открытие браузера
    threading.Timer(1, open_browser).start()
    uvicorn.run(app, host="0.0.0.0", port=8000)
