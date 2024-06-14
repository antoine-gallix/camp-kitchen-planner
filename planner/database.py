import peewee

from planner import logger
from planner.config import config


class DB:
    _instance = None

    def __new__(cls):
        if not cls._instance:
            if config.get("in_memory", False):
                db_url = ":memory:"
                logger.debug("using in-memory database")
            else:
                db_url = config.get("database_file", "database.db")
                logger.debug(f"using database file: {db_url}")
            cls._instance = peewee.SqliteDatabase(db_url)
        return cls._instance
