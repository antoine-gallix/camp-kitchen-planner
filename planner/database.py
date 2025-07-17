import peewee

from planner import logger
from planner.config import config


class DB:
    """Singleton Database Object

    # usage
    db=DB()
    
    """
    _instance = None

    @staticmethod
    def connect():
        if config.get("in_memory", False):
            db_url = ":memory:"
            logger.debug("using in-memory database")
        else:
            db_url = config.get("database_file", "database.db")
            logger.debug(f"using database file: {db_url}")
        return peewee.SqliteDatabase(db_url)
        

    def __new__(cls):
        if not cls._instance:
            logger.debug("connecting to database")
            cls._instance = cls.connect()
        return cls._instance
