import logging
import os
import sys
import threading

import uvicorn
import webview
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from starlette.responses import JSONResponse

from settings import Settings, settings
from utils import scan_ips
from models import ServerInfo

app = FastAPI()
logging.basicConfig(
    filename='log.txt',
    level=logging.INFO,
    encoding='utf-8',
    format='%(asctime)s %(levelname)s: %(message)s'
)


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


@app.exception_handler(Exception)
async def all_exception_handler(request, exc):
    logging.exception(f"Unhandled error: {exc}")
    return JSONResponse(status_code=500, content={"detail": "Internal server error (known)"})


def start_api():
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="debug")


if __name__ == '__main__':
    threading.Thread(target=start_api, daemon=True).start()
    webview.create_window("MCPing", "http://127.0.0.1:8000", width=1200, height=800, text_select=True,)
    webview.settings['OPEN_DEVTOOLS_IN_DEBUG'] = False
    webview.start(debug=True, private_mode=False)

