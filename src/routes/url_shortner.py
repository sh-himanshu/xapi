import re
import secrets
from datetime import datetime
from typing import Optional

from fastapi import Query, Request
from fastapi.exceptions import HTTPException
from fastapi.responses import (PlainTextResponse, RedirectResponse,
                               UJSONResponse)

from .. import app, xbot

URL_SHORTNER = xbot.db.collection("URL_SHORTNER")
_SLUG_REGEX = re.compile(r"^[\@\w-]{4,25}$")


def check_slug(slug: str) -> bool:
    return _SLUG_REGEX.match(slug) and (slug.count("_") + slug.count("-")) < 8


@app.get("/short", response_class=PlainTextResponse)
async def url_shortner(
    request: Request,
    url: str,
    slug: Optional[str] = Query(
        None,
        title="slug",
        description="Custom Key",
        max_length=25,
    ),
):
    if slug:
        if not check_slug(slug):
            raise HTTPException(400, "SLUG_INVALID !")
        if await URL_SHORTNER.find_one({"key": slug}):
            raise HTTPException(400, "SLUG_ALREADY_EXIST !")
        key = slug
    else:
        key = secrets.token_urlsafe(5)
    host = f"https://{request.headers.get('host')}"
    await URL_SHORTNER.insert_one(
        {
            "key": key,
            "short": f"{host}/s/{key}",
            "original_url": url,
            "views": 0,
            "created_at": datetime.now().strftime("%m/%d/%Y, %H:%M:%S"),
        }
    )
    return f"{host}/s/{key}"


@app.get("/v/{key}", response_class=UJSONResponse, include_in_schema=False)
async def view_url_info(key: str):
    if not check_slug(key):
        return {"error": f"InvalidKey: '{key}' is not Supported !"}

    if found := await URL_SHORTNER.find_one({"key": key}):
        del found["_id"]
        return found
    return {"error": f"KeyError: '{key}' Doesn't exist in Database."}


@app.get("/s/{key}", include_in_schema=False)
async def get_url(key: str):
    if not check_slug(key):
        raise HTTPException(409, f"InvalidKey: '{key}' is not Supported !")
    found = await URL_SHORTNER.find_one({"key": key})
    if not found:
        raise HTTPException(404, "NOT_FOUND")
    return RedirectResponse(found.get("original_url"))
