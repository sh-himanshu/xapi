import logging
import re
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Union

import ujson
from bs4 import BeautifulSoup
from fastapi import APIRouter
from fastapi.responses import RedirectResponse, UJSONResponse

from .. import app, xbot
from ..utils import run_sync

ResultsList = List[Dict[str, Optional[str]]]
logger = logging.getLogger(__name__)
router = APIRouter(prefix="/anime", tags=["Gogo Anime"])


class AnimeScrapper(ABC):
    @abstractmethod
    async def search(self, query: str):
        pass

    @abstractmethod
    async def get_episodes(self, media_id: str):
        pass

    @abstractmethod
    async def get_sources(self, ep_id: str):
        pass


class Extractor:
    def __init__(self) -> None:
        self.r_streamtape = re.compile(
            r"document\.getElementById\([a-z+'\s\"]+\)\.innerHTML\s=\s\"([\/\w.=-?&]+)\"\s\+\s'([\/\w.=-?&]+)';"
        )
        self.r_vidcdn = re.compile(
            r"playerInstance\.setup\({(?:\s+)?sources:\[{file:\s'(https://[&+?=\w./-]+).+}\](?:\s+)?}\);"
        )
        super().__init__()

    async def streamtape(self, url: str) -> Optional[str]:
        async with xbot.http.get(url) as resp:
            if resp.status == 200:
                text = await resp.text()
                if match := self.r_streamtape.search(text):
                    return f"http:{match.group(1)}{match.group(2)}"

    async def vidcdn(self, url: str) -> Optional[str]:
        if page := await self.get(url):
            if match := self.r_vidcdn.search(
                page.find("div", {"class": "videocontent"})
                .find("script", {"type": "text/JavaScript"})
                .string
            ):
                return match.group(1)


class Gogo(AnimeScrapper, Extractor):
    def __init__(self) -> None:
        self.base_url = "https://gogoanime.pe/"
        self.base_url_cdn = "https://ajax.gogo-load.com/"
        self.thumb_regex = re.compile(r"https://[/\w.-]+.(?:png|jpe?g)")
        super().__init__()

    async def get(
        self,
        url: str,
        mode: str = "",
        params: Optional[Dict[str, Union[str, int]]] = None,
    ) -> Optional[BeautifulSoup]:
        async with xbot.http.get(url, params=params) as resp:
            logger.debug(f"GET - {resp.url} - status {resp.status}")
            if resp.status == 200:
                text = await resp.text()
                if mode == "search":
                    text = ujson.loads(text).get("content")
                return await self.soupify(text)

    @run_sync
    def soupify(self, text: str) -> BeautifulSoup:
        return BeautifulSoup(text, "lxml")

    async def search(self, query: str) -> Optional[ResultsList]:
        search_url = f"{self.base_url_cdn}site/loadAjaxSearch"
        params = {"id": -1, "keyword": query, "link_web": self.base_url}
        page = await self.get(search_url, "search", params)
        search_results: ResultsList = []
        for result in page.findAll("a", {"class": "ss-title"}):
            thumbnail = (
                match.group(0)
                if (match := self.thumb_regex.search(result.div.get("style")))
                else None
            )
            result_href = result.get("href")
            search_results.append(
                {
                    "media_id": result_href.rsplit("/", 1)[1],
                    "name": result.text.strip(),
                    "link": result_href,
                    "thumb": thumbnail,
                }
            )
        return {"results": search_results}

    async def get_episodes(
        self, media_id: str, detailed: bool = True
    ) -> Optional[Dict[str, Union[str, ResultsList, int]]]:
        if media_id.startswith("https://"):
            media_url = media_id
        else:
            media_url = f"{self.base_url}category/{media_id}"

        if page := await self.get(media_url):
            hidden_data = page.findAll("input", {"type": "hidden"})
            params = {
                key: value
                for x in hidden_data
                if (key := x.get("id")) and (value := x.get("value"))
            }
            params["id"] = params.pop("movie_id")
            params["ep_start"] = 0
            # https://github.com/anime-dl/anime-downloader/.../gogoanime.py#L87
            params["ep_end"] = 99999
            episode_url = f"{self.base_url_cdn}ajax/load-list-episode"
            ep_page = await self.get(episode_url, params=params)
            out = {
                "media_id": media_id.rsplit("/", 1)[1] if "/" in media_id else media_id
            }
            if detailed:
                ep_list: ResultsList = []
                for ep_a in reversed(ep_page.findAll("a")):
                    ep_num = int(
                        ep_a.find("div", {"class": "name"}).text.replace("EP", "")
                    )
                    ep_link = self.base_url + ep_a.get("href").split("/", 1)[1]
                    ep_list.append(
                        {
                            "ep": ep_num,
                            "ep_id": ep_link.rsplit("/", 1)[1],
                            "type": ep_a.find("div", {"class": "cate"}).text.strip(),
                            "link": ep_link,
                        }
                    )
                out["episodes"] = ep_list
                out["total"] = len(ep_list)
            else:
                out["total"] = int(
                    ep_page.findAll("a")[0]
                    .find("div", {"class": "name"})
                    .text.replace("EP", "")
                )
            return out

    async def get_sources(
        self, ep_id: str, direct_link: bool
    ) -> Optional[Dict[str, str]]:
        if ep_id.startswith("https://"):
            episode_url = ep_id
        else:
            episode_url = f"{self.base_url}{ep_id}"
        if page := await self.get(episode_url):
            cdns = page.find("div", {"class": "anime_muti_link"}).findAll("li")
            sources = dict(
                map(lambda x: ("_".join(x.get("class")), x.a.get("data-video")), cdns)
            )
            sources.pop("anime", None)
            if (streamani := sources.get("vidcdn", "")).startswith("//"):
                sources["vidcdn"] = "https:" + streamani
            if direct_link:
                return {
                    "streamtape": await self.streamtape(sources.pop("streamtape")),
                    "vidcdn": await self.vidcdn(sources.pop("vidcdn")),
                }
            return sources


anime_dl = Gogo()


@router.get("/search", response_class=UJSONResponse)
async def anime_search(q: str):
    return await anime_dl.search(q) or {"error": "Not Found !"}


@router.get("/{media_id}/episodes", response_class=UJSONResponse)
async def find_episodes(media_id: str, detailed: bool = True):
    return await anime_dl.get_episodes(media_id, detailed) or {"error": "Not Found !"}


@router.get("/{media_id}/ep/{num}")
async def episode_by_media_id(media_id: str, num: int, direct_link: bool = False):
    return RedirectResponse(
        f"/anime/{media_id}-episode-{num}?direct_link={direct_link}"
    )


@router.get("/{ep_id}")
async def episode_by_episode_id(ep_id: str, direct_link: bool = False):
    return await anime_dl.get_sources(ep_id, direct_link) or {"error": "Not Found !"}


app.include_router(router)
