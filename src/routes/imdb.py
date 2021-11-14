import logging
import re
import traceback
from typing import Any, Dict, List, Optional, Tuple

import ujson
from bs4 import BeautifulSoup
from fastapi import APIRouter, Query
from fastapi.responses import UJSONResponse

from .. import app, xbot
from ..utils import run_sync

router = APIRouter(prefix="/imdb", tags=["IMDB"])

IMDB_RESULT_TEXT = re.compile(r"\((?P<year>\d+)\)(?:\s\((?P<media>[A-Za-z\s]+)\))?")
logger = logging.getLogger(__name__)


@router.get("/", response_class=UJSONResponse)
async def imdb_search(
    q: str = Query(..., title="q", description="Search query."),
    limit: int = Query(10, title="limit", description="Result limit."),
    filter_by: str = Query(
        "all",
        title="filter_by",
        description="Choose category i.e. (all, movie, tv, episode, game)",
    ),
    exact: bool = Query(False, title="exact", description="Show only exact matches."),
    image_size: int = Query(
        1080, title="image_size", description="Thumbnail size. (0 - original)"
    ),
):
    imdb = xbot.config.imdb.get("url")
    ttype_dict = xbot.config.imdb.get("ttype_dict")
    limit = max(limit, 1)
    imdb_search = f"{imdb}/find"
    params = {"q": q, "s": "tt", "exact": "true" if exact else "false"}
    if (
        filter_by
        and (filter_by != "all")
        and (ttype := ttype_dict.get(filter_by.lower()))
    ):
        params["ttype"] = ttype
    async with xbot.http.get(imdb_search, params=params) as resp:
        if resp.status != 200:
            return {"error": f"Failed to Get '{imdb_search}'", "status": resp.status}
        page = await resp.text()
    search_results: List[Dict[str, Optional[str]]] = []
    if not (
        result_table := BeautifulSoup(page, "lxml").find("table", {"class": "findList"})
    ):
        return {"error": f"No Result Found for Query: '{q}' => ({imdb_search})"}

    for i, result in enumerate(result_table.findAll("tr", {"class": "findResult"})):
        if i >= limit:
            break
        image_td_ = result.find("td", {"class": "primary_photo"})
        result_page = image_td_.a.get("href")
        img_src_ = image_td_.a.img.get("src")
        if img_src_.endswith("85lhIiFCmSScRzu.png"):
            image = None
        else:
            image = f"{img_src_.rsplit('._V1_', 1)[0]}._V1_" + (
                ".jpg"
                if image_size == 0
                else f"UX{min(3840, max(image_size, 360))}.jpg"
            )
        result_text_ = result.find("td", {"class": "result_text"})
        title = result_text_.a.text
        if match := IMDB_RESULT_TEXT.search(result_text_.text):
            year = int(match.group("year"))
            media_type = match.group("media")
        else:
            year, media_type = None, None
        search_results.append(
            {
                "@id": result_page.split("/")[2],
                "title": title,
                "year": year,
                "@type": media_type or "Movie",
                "url": f"{imdb}{result_page}",
                "image": image,
            }
        )
    return {"results": search_results}


@router.get("/{id}", response_class=UJSONResponse)
async def imdb_info(id: str, video: bool = False):
    imdb = xbot.config.imdb.get("url")
    imdb_title = f"{imdb}/title/{id}/"
    async with xbot.http.get(imdb_title) as resp:
        if resp.status != 200:
            return {"error": f"Failed to Get '{imdb_title}'", "status": resp.status}
        page = await resp.text()
    soup = BeautifulSoup(page, "lxml")
    if json_data := soup.find("script", {"type": "application/ld+json"}).string:
        out = ujson.loads(json_data)
        if (
            video
            and (tr_info := out.get("trailer"))
            and tr_info["@type"] == "VideoObject"
        ):
            out["trailer"]["video"] = await get_title_trailer(
                f"{imdb}{tr_info['embedUrl']}"
            )

        return await beautify_res(out)
    return {"error": "UnKnown Error"}


async def get_title_trailer(video_url: str) -> Optional[List[Dict[str, str]]]:
    async with xbot.http.get(video_url) as resp:
        if resp.status != 200:
            logger.error(
                {"error": f"Failed to Get '{video_url}'", "status": resp.status}
            )
            return
        page = await resp.text()
    soup = BeautifulSoup(page, "lxml")
    video_data = None
    for src in soup.findAll("script", type="text/javascript"):
        if not (src_text := src.string):
            continue
        if ("videoLegacyAdUrl" in src_text) or ("var args =" in src_text):
            for line in src_text.splitlines(False):
                if "var args =" in line:
                    try:
                        video_data = ujson.loads(
                            ujson.loads(line[line.find("{") : line.rfind("}") + 1])[
                                "playbackData"
                            ][0]
                        )[0]["videoLegacyEncodings"]
                    except Exception as exc:
                        logger.error(
                            "".join(
                                traceback.format_exception(
                                    etype=type(exc), value=exc, tb=exc.__traceback__
                                )
                            )
                        )
                        continue
                    else:
                        break
    return video_data


@run_sync
def beautify_res(out):
    return formatObj(out)


def formatObj(obj: Any) -> Any:
    if isinstance(obj, (List, Tuple)):
        return [formatObj(x) for x in obj]
    if isinstance(obj, Dict):
        keys = obj.keys()
        for i in ("embedUrl", "url"):
            if i in keys and obj[i].startswith("/"):
                obj[i] = f"https://www.imdb.com{obj[i]}"
        if "@context" in keys:
            del obj["@context"]
        return {x: formatObj(y) for x, y in obj.items()}
    return obj


app.include_router(router)
