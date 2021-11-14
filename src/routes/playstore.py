from typing import Dict, List, Union

from bs4 import BeautifulSoup
from fastapi.responses import UJSONResponse

from .. import app, xbot


@app.get("/playstore", response_class=UJSONResponse)
async def playstore_search(q: str, limit: int = 10):
    pstore = xbot.config.playstore
    limit = max(limit, 1)
    link = f"{pstore}/store/search?q={q}&c=apps"
    async with xbot.http.get(link) as resp:
        if resp.status != 200:
            return {"error": f"Failed to Get '{link}'", "status": resp.status}
        page = await resp.text()

    search_results: List[Dict[str, Union[str, Dict[str, str]]]] = []
    for i, app in enumerate(
        (
            BeautifulSoup(page, "lxml")
            .find("div", {"class": "ZmHEEd"})
            .findAll("div", {"class": "ImZGtf mpg5gc"})
        )
    ):
        if i >= limit:
            break
        app_info_ = app.find("div", {"class": "WsMG1c nnK0zc"})
        app_name = app_info_.get("title")
        app_link = app_info_.find_previous("a").get("href")
        package = app_link.rsplit("=", 1)[1]
        dev_info_ = app.find("a", {"class": "mnKHRc"})
        dev_name = dev_info_.find("div", {"class": "KoLSrc"}).text
        dev_link = dev_info_.get("href")
        # stars = app.find("div", {"role": "img"}).get("aria-label").split()[1]
        if star_div := app.find("div", {"role": "img"}):
            stars = star_div.get("aria-label").split()[1]
        else:
            stars = "0"
        image = (
            app.find("img", {"class": "T75of QNCnCf"})
            .get("data-src")
            .replace("=s128", "=s512")
        )
        search_results.append(
            {
                "app": {"name": app_name, "link": f"{pstore}{app_link}"},
                "package": package,
                "developer": {"name": dev_name, "link": f"{pstore}{dev_link}"},
                "image": image,
                "stars": stars,
            }
        )
    return {"results": search_results}
