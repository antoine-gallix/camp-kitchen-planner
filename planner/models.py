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


class Ingredient(BaseModel):
    name = peewee.CharField(unique=True)
    unit = peewee.CharField()

    def __str__(self):
        return self.name

    @classmethod
    def exists(cls, name):
        return cls.get_or_none(cls.name == name) is not None


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
    quantity = peewee.FloatField()

    def __repr__(self):
        return f"Item({self.quantity},{self.ingredient})"

    def __str__(self):
        return f"{self.quantity} {self.ingredient.name}"

    @staticmethod
    def parse_item_line(line):
        # pre-process
        line = line.lower()
        line = re.sub(r"\s+", " ", line)  # conpact spaces
        line = line.strip()  # remove border spaces

        # regexes
        UNIT_SYMBOLS = ["g", "kg", "L", "l", "ml", "cl", "tsp", "tbsp"]
        UNIT_SYMBOL_REGEX = f"({'|'.join(UNIT_SYMBOLS)})"
        NUMBER_REGEX = r"[\d\.]+"
        QUANTITY_REGEX = NUMBER_REGEX + r"\s?" + f"{UNIT_SYMBOL_REGEX}?" + r"(?=\s)"
        PARENTHESIS_REGEX = r"\((.*)\)"

        # extract quantity
        res = re.search(QUANTITY_REGEX, line)
        if res is not None:
            quantity = res.group()
            rest = line[res.end() :].strip()
        else:
            raise Exception(f"quantity string not found in {line!r}")
        # extract number
        res = re.search(NUMBER_REGEX, quantity)
        number = float(res.group())
        unit = quantity[res.end() :].strip() or None

        if number == 0:
            raise Exception(f"parsed number is zero in line {line}")

        # extract parenthesis
        res = re.search(PARENTHESIS_REGEX, rest)
        if res is not None:
            ingredient = rest[: res.start()].strip()
        else:
            ingredient = rest
        return ingredient, number, unit

    @staticmethod
    def normalize(number, unit):
        print("normalizing")
        unit_map = {
            "mg": ("g", 1 / 1000),
            "g": ("g", 1),
            "kg": ("g", 1000),
            "ml": ("l", 1 / 1000),
            "cl": ("l", 1 / 100),
            "dl": ("l", 1 / 10),
            "l": ("l", 1),
            None: ("unit", 1),
            "": ("unit", 1),
        }
        unit, scale = unit_map[unit]
        number = number * scale
        return number, unit

    @classmethod
    def create_item_from_line(cls, line, recipe):
        name, number, unit = cls.parse_item_line(line)

        number, unit = cls.normalize(number, unit)
        ingredient, created = Ingredient.get_or_create(name=name, unit=unit)
        if created:
            print(f"Ingredient has been created")
        else:
            print(f"Ingredient already exist")
        item = cls.create(ingredient=ingredient, quantity=number, recipe=recipe)
        print(f"created item: {item}")
        return item


all_models = [Ingredient, Recipe, Item]


def create_tables():
    print("creating tables")
    db.create_tables(all_models)


def reset_tables():
    print("reseting tables")
    db.drop_tables(all_models)
    db.create_tables(all_models)
