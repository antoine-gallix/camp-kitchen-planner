import re
from enum import Enum, auto

import peewee

from config import config

if config.get("in_memory", False):
    db_url = ":memory:"
    print("using in-memory database")
else:
    db_url = config.get("database_file", "database.db")
    print(f"using database file: {db_url}")

db = peewee.SqliteDatabase(db_url)


class BaseModel(peewee.Model):
    class Meta:
        database = db


class WeightUnit(Enum):
    g = auto()
    kg = auto()


class VolumeUnit(Enum):
    ml = auto()
    cl = auto()
    dl = auto()
    l = auto()


class Ingredient(BaseModel):
    name = peewee.CharField(unique=True)
    type = peewee.CharField()

    def __str__(self):
        return self.name


class Recipe(BaseModel):
    name = peewee.CharField(unique=True)
    serves = peewee.IntegerField()

    def __str__(self):
        return str(self.name)

    @property
    def description(self):
        description_ = [str(self)]
        for item in getattr(self, "items"):
            description_.append(
                f"- {item.quantity} {item.ingredient.unit} {item.ingredient.name}"
            )
        return "\n".join(description_)

    @classmethod
    def exists(cls, name):
        return cls.get_or_none(cls.name == name) is not None


class Item(BaseModel):
    recipe = peewee.ForeignKeyField(Recipe, backref="items")
    ingredient = peewee.ForeignKeyField(Ingredient)
    quantity = peewee.IntegerField()

    @staticmethod
    def parse_item_line(line):
        # pre-process
        line = line.lower()
        line = re.sub(r"\s+", " ", line)  # conpact spaces
        line = line.strip()  # remove border spaces

        # regexes
        UNIT_SYMBOLS = ["g", "kg", "L", "l", "ml", "cl", "tsp", "tbsp"]
        UNIT_SYMBOL_REGEX = f"({'|'.join(UNIT_SYMBOLS)})"
        QUANTITY_REGEX = r"\d+" + r"\s?" + f"{UNIT_SYMBOL_REGEX}?"
        PARENTHESIS_REGEX = r"\((.*)\)"

        # extract quantity
        res = re.search(QUANTITY_REGEX, line)
        if res is not None:
            quantity = res.group()
            rest = line[res.end() :].strip()
        else:
            raise Exception(f"quantity string not found in {line!r}")

        # extract number
        res = re.search(r"\d+", quantity)
        number = int(res.group())
        unit = quantity[res.end() :].strip() or None

        # extract parenthesis
        res = re.search(PARENTHESIS_REGEX, rest)
        if res is not None:
            ingredient = rest[: res.start()].strip()
        else:
            ingredient = rest
        return ingredient, int(number), unit

    @classmethod
    def from_string(cls, item_string):
        return cls.__init__()


all_models = [Ingredient, Recipe, Item]


def create_tables():
    print("creating tables")
    db.create_tables(all_models)


def reset_tables():
    print("reseting tables")
    db.drop_tables(all_models)
    db.create_tables(all_models)
