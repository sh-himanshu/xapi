from typing import Optional

import aiohttp
import ujson


class AioHttp:
    _session: Optional[aiohttp.ClientSession]

    def __init__(self):
        self._session = None
        super().__init__()

    @property
    def _is_active(self) -> bool:
        return self._session and not self._session.closed

    @property
    def http(self) -> aiohttp.ClientSession:
        if not self._is_active:
            self._session = self.gen_new_session()
        return self._session

    def gen_new_session(self) -> aiohttp.ClientSession:
        return aiohttp.ClientSession(json_serialize=ujson.dumps)

    async def close_session(self) -> None:
        if self._is_active:
            await self._session.close()
