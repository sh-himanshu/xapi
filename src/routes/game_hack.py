import re

from fastapi import Query
from fastapi.responses import UJSONResponse

from .. import app, xbot

GAME_URL = re.compile(
    r"^https://tbot\.xyz/(?P<game>\w+)/#(?P<data>[\w=]+)(?:&|\?)tgShareScoreUrl"
)


_game_default_headers = {
    "Connection": "keep-alive",
    "sec-ch-ua": '" Not;A Brand";v="99", "Google Chrome";v="91", "Chromium";v="91"',
    "sec-ch-ua-mobile": "?0",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Content-Type": "text/plain;charset=UTF-8",
    "Accept": "*/*",
    "Origin": "https://tbot.xyz",
    "Sec-Fetch-Site": "same-origin",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Dest": "empty",
    "Accept-Language": "en-US,en;q=0.9",
}


@app.get("/gamehack", response_class=UJSONResponse)
async def hack_game_score(
    url: str = Query(
        ...,
        title="url",
        description="Game URL (click on the game button and copy url from browser)",
        regex=GAME_URL.pattern,
    ),
    score: int = Query(
        ..., title="score", description="Desired score (don't set too high xD)"
    ),
):
    if not (match := GAME_URL.search(url)):
        return {"error": "Invalid URL"}
    data = {"data": match.group("data"), "score": str(score)}
    headers = {"Referer": f"https://tbot.xyz/{match.group('game')}"}
    headers.update(_game_default_headers)
    async with xbot.http.post(
        xbot.config.tg_game_api, headers=headers, data=data
    ) as resp:
        try:
            out = await resp.json()
        except Exception:
            return {"error": "Something went wrong", "msg": await resp.text()}
        return out
