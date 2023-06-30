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


def normalize_string(string):
    return re.sub("\s{2,}", " ", string.lower().strip())


class BaseModel(peewee.Model):
    class Meta:
        database = db


class Ingredient(BaseModel):
    name = peewee.CharField()
    unit = peewee.CharField()
    price = peewee.FloatField(null=True)

    valid_units = ["kg", "l", "tsp", "tbsp", "unit"]

    class Meta:
        indexes = [(("name", "unit"), True)]

    def __init__(self, **kwargs):
        if (unit := kwargs["unit"]) not in self.valid_units:
            raise ValueError(f"unit not valid {unit!r}")
        kwargs["name"] = normalize_string(kwargs["name"])
        super().__init__(**kwargs)

    def __str__(self):
        return str(self.name)

    def __repr__(self):
        return f"<Ingredient(name={self.name},unit={self.unit})>"

    @classmethod
    def exists(cls, name):
        return cls.get_or_none(cls.name == name) is not None

    def dump(self):
        dump_ = dict(name=self.name, unit=self.unit)
        if self.price is not None:
            dump_["price"] = self.price
        return dump_


class Recipe(BaseModel):
    name = peewee.CharField(unique=True)
    serves = peewee.IntegerField()
    instructions = peewee.CharField(null=True)

    def __init__(self, **kwargs):
        if "name" in kwargs:
            kwargs["name"] = normalize_string(kwargs["name"])
        super().__init__(**kwargs)

    def __str__(self):
        return f"{self.name} ({self.serves} persons)"

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

    def full(self):
        lines = []
        lines.append(f"serves: {self.serves}")
        lines.append("---")
        for item in self.items:
            lines.append(f"- {item.quantity}{item.ingredient.unit} {item.ingredient}")
        if self.instructions is not None:
            lines.append("---")
            lines.append(self.instructions)

        return "\n".join(lines)

    def rescale(self, servings):
        ...


class RecipeItem(BaseModel):
    recipe = peewee.ForeignKeyField(Recipe, backref="items")
    ingredient = peewee.ForeignKeyField(Ingredient)
    quantity = peewee.FloatField()

    def __repr__(self):
        return f"Item({self.quantity},{self.ingredient}({self.ingredient.unit}))"

    def __str__(self):
        return f"{self.quantity}{self.ingredient.unit} {self.ingredient.name}"

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
        unit_map = {
            "mg": ("kg", 1e-6),
            "g": ("kg", 1e-3),
            "kg": ("kg", 1),
            "ml": ("l", 1e-3),
            "cl": ("l", 1e-2),
            "dl": ("l", 1e-1),
            "l": ("l", 1),
            None: ("unit", 1),
            "": ("unit", 1),
            "tbsp": ("tbsp", 1),
            "tsp": ("tsp", 1),
        }
        unit, scale = unit_map[unit]
        number *= scale
        return number, unit

    @classmethod
    def create_item_from_line(cls, line, recipe):
        name, number, unit = cls.parse_item_line(line)

        number, unit = cls.normalize(number, unit)
        ingredient, created = Ingredient.get_or_create(name=name, unit=unit)
        if created:
            logger.debug("Ingredient has been created")
        else:
            logger.debug("Ingredient already exist")
        item = cls.create(ingredient=ingredient, quantity=number, recipe=recipe)
        logger.debug(f"created item: {item}")
        return item


class Project(BaseModel):
    name = peewee.CharField(unique=True)
    servings = peewee.IntegerField()

    def __str__(self):
        return f"{self.name} for {self.servings} persons"

    def __repr__(self):
        return f"Project({self.__str__()})"

    @property
    def recipes(self):
        return (dish.recipe for dish in self.dishes)

    def shopping_list(self):
        shopping_list = defaultdict(float)
        for recipe in self.recipes:
            for item in recipe.items:
                shopping_list[item.ingredient] += (
                    item.quantity * self.servings / recipe.serves
                )
        return shopping_list

    def priced_shopping_list(self):
        shopping_list = self.shopping_list()
        priced_shopping_list = [
            (
                ingredient,
                quantity,
                ingredient.price * quantity if ingredient.price is not None else None,
            )
            for ingredient, quantity in shopping_list.items()
        ]
        return priced_shopping_list

    def print_summary(self):
        print(self)
        for recipe in self.recipes:
            print(f"- {recipe.name}")

    def print_shopping_list(self):
        t = PrettyTable()
        t.field_names = [
            "ingredient",
            "quantity",
            "price",
        ]

        for ingredient, quantity, price in self.priced_shopping_list():
            main = f"{ingredient}: {quantity:g}{ingredient.unit}"
            if price is not None:
                price_str = f"({price} euros)"
            else:
                price_str = f"(no price data)"
            t.add_row((ingredient.name, f"{quantity:.1f} {ingredient.unit}", price_str))
        print(t)

    def print_csv_shopping_list(self):
        t = PrettyTable()

        t.field_names = [
            "ingredient",
            "unit",
            "quantity",
            "price",
        ]

        for ingredient, quantity, price in self.priced_shopping_list():
            t.add_row(
                (str(ingredient.name), str(ingredient.unit), quantity, ingredient.price)
            )
        print(t.get_csv_string())

    def print_scaled(self):
        print(self)
        print()
        for recipe in self.recipes:
            print(f"{recipe}")
            for item in recipe.items:
                print(
                    f"- {item.quantity * self.servings / recipe.serves} {item.ingredient.unit} {item.ingredient}"
                )


class ProjectItem(BaseModel):
    project = peewee.ForeignKeyField(Project, backref="dishes")
    recipe = peewee.ForeignKeyField(Recipe)

    def __repr__(self):
        return f"<ProjectItem({self.recipe} in {self.project})>"


all_models = [Ingredient, Recipe, RecipeItem, Project, ProjectItem]


def create_tables():
    logger.debug("creating tables")
    db.create_tables(all_models)


def reset_tables():
    logger.debug("reseting tables")
    db.drop_tables(all_models)
    db.create_tables(all_models)
