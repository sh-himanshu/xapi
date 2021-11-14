from typing import Dict

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorCollection


class Database:
    def __init__(self, db_uri: str) -> None:
        # Ignoring Certificate check as mongo being wierd
        self.client = AsyncIOMotorClient(
            db_uri, tls=True, tlsAllowInvalidCertificates=True
        )
        self._db = self.client["xapi"]

    def collection(self, name: str) -> AsyncIOMotorCollection:
        return self._db[name]

    async def reset(self, hard: bool = False) -> None:
        if hard:
            # Delete All Databases
            db_list = await self.client.list_database_names()
            for dbname in db_list:
                if dbname not in ["admin", "local"]:
                    await self.client.drop_database(dbname)
        else:
            # Delete All Collections from "xapi"
            col_list = await self._db.list_collection_names()
            for col in col_list:
                await self._db.drop_collection(col)

    @staticmethod
    def mongo_obj(id: str) -> Dict[str, ObjectId]:
        return {"_id": ObjectId(id)}

    def close(self) -> None:
        self.client.close()
