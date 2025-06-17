import os
import sys
import threading

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles


from config import TARGET_IPS
from utils import scan_ip, ServerInfo, strip_ansi

app = FastAPI()


if getattr(sys, 'frozen', False):  # Если упаковано в .exe
    # временная папка, куда PyInstaller распаковывает ресурсы
    base_dir = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
else:
    base_dir = os.path.dirname(os.path.abspath(__file__))

templates = Jinja2Templates(directory=os.path.join(base_dir, "templates"))
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/servers")
async def api_servers():
    servers: list[ServerInfo] = []
    for ip in TARGET_IPS:
        results = await scan_ip(ip)
        for result in results:
            result["motd"] = strip_ansi(result["motd"])
        servers.extend(results)
    return {"servers": servers}


def open_browser():
    import webbrowser
    webbrowser.open("http://127.0.0.1:8000")

if __name__ == "__main__":
    # Авто‑открытие браузера
    threading.Timer(1, open_browser).start()
    uvicorn.run(app, host="0.0.0.0", port=8000)
