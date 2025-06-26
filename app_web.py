import os
import sys
import threading

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from settings import Settings, settings
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


@app.get("/settings")
def get_settings():
    return settings

@app.post("/settings")
def update_settings(new_settings: Settings):
    settings.target_ips = new_settings.target_ips
    settings.port_start = new_settings.port_start
    settings.port_end = new_settings.port_end
    settings.timeout = new_settings.timeout
    settings.concurrency_limit = new_settings.concurrency_limit
    settings.save()
    return {"status": "ok"}


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/servers")
async def api_servers():
    servers: list[ServerInfo] = []
    results = await scan_ips(settings.target_ips)
    servers.extend(results)
    return {"servers": servers}


def open_browser():
    import webbrowser
    webbrowser.open("http://127.0.0.1:8000")

if __name__ == "__main__":
    # Авто‑открытие браузера
    threading.Timer(1, open_browser).start()
    uvicorn.run(app, host="0.0.0.0", port=8000)
