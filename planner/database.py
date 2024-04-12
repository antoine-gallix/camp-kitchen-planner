import re
from collections import defaultdict

import peewee
from prettytable import PrettyTable

from planner import logger
from planner.config import config

if config.get("in_memory", False):
    db_url = ":memory:"
    logger.debug("using in-memory database")
else:
    db_url = config.get("database_file", "database.db")
    logger.debug(f"using database file: {db_url}")

db = peewee.SqliteDatabase(db_url)
