import asyncio
from typing import Any, Dict, Union

import feedparser
from fastapi.responses import UJSONResponse

from .. import app, xbot
from ..utils import run_sync

REQ_KEYS = ("source", "published", "title", "summary", "id", "link")


@run_sync
def filter_entry(entry: Dict[str, Any]) -> Dict[str, Union[Dict[str, str], str]]:
    for key in list(entry):
        if key not in REQ_KEYS:
            del entry[key]

    return entry


@app.get("/news", response_class=UJSONResponse)
async def news_feed(q: str = "news", limit: int = 10):
    url = xbot.config.news_feed + q
    async with xbot.http.get(url) as resp:
        if resp.status != 200:
            return {"error": f"Failed to Get '{url}'", "status": resp.status}
        rss_feed = resp.url
        page = await resp.text()
    entries = feedparser.parse(page).entries
    out = await asyncio.gather(
        *map(filter_entry, entries[:limit] if limit > 0 else entries)
    )
    return {"rss": str(rss_feed), "results": out}
