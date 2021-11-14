import asyncio
import logging

from .aio_http import AioHttp
from .constants import Constants
from .database import Database


class XBot(AioHttp):
    def __init__(self):
        self.config = Constants()
        self.db = Database(self.config.mongodb_uri)
        self.log = logging.getLogger("Xbot")
        self.loop = asyncio.get_event_loop()
        super().__init__()

    async def start(self):
        # Hard Reset DB
        # await self.db.reset(hard=True)
        self.log.info("XAPI has Started !")

    async def stop(self):
        self.log.info("Closing http session...")
        await self.close_session()
        self.db.close()
