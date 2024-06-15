import re
from collections import defaultdict
from typing import Self

import funcy
import peewee
from prettytable import PrettyTable
from rich import print

from planner import logger
from planner.database import DB
from planner.errors import QueryError
from planner.parse import Unit, normalize_string, parse_recipe_file


class BaseModel(peewee.Model):
    class Meta:
        database = DB()


class UnitField(peewee.CharField):
    def db_value(self, unit: Unit):
        return str(unit)

    def python_value(self, value):
        return Unit(value)


class Tag(BaseModel):
    """Classify ingredients."""

    name = peewee.CharField(unique=True)

    def __str__(self) -> str:
        return str(self.name)

    def __repr__(self) -> str:
        return f"<Tag({self.name!r})>"


class Ingredient(BaseModel):
    """Ingredient to be used in recipes. Have a fixed unit of count and price"""

    name = peewee.CharField()
    unit = UnitField()
    price = peewee.FloatField(null=True)

    _list_fields = ["id", "name", "unit", "tags"]

    class Meta:
        indexes = [(("name", "unit"), True)]

    def __init__(self, **kwargs) -> None:
        if (unit := kwargs.get("unit")) is not None and not isinstance(unit, Unit):
            kwargs["unit"] = Unit(unit)
        if (name := kwargs.get("name")) is not None:
            kwargs["name"] = normalize_string(name)
        super().__init__(**kwargs)

    def __str__(self) -> str:
        return str(self.name)

    def __repr__(self) -> str:
        return f"<Ingredient(name={self.name},unit={self.unit})>"

    @classmethod
    def exists(cls, name) -> bool:
        return cls.get_or_none(cls.name == name) is not None

    def add_tag(self, tag: Tag):
        IngredientTag.create(ingredient=self, tag=tag)

    @property
    def tags(self):
        return list(
            Tag.select()
            .join(IngredientTag)
            .join(Ingredient)
            .where(Ingredient.id == self.id)
        )

    def dump(self) -> dict:
        dump_ = dict(name=self.name, unit=str(self.unit))
        if self.price is not None:
            dump_["price"] = self.price
        if self.tags:
            dump_["tags"] = [str(tag) for tag in self.tags]
        return dump_


class IngredientTag(BaseModel):
    """Link ingredients to tags"""

    ingredient = peewee.ForeignKeyField(Ingredient)
    tag = peewee.ForeignKeyField(Tag)

    class Meta:
        indexes = [(("ingredient", "tag"), True)]


class Recipe(BaseModel):
    """Ingredient, quantities and instructions"""

    name = peewee.CharField(unique=True)
    serves = peewee.IntegerField()
    instructions = peewee.CharField(null=True)

    _list_fields = ["id", "name", "serves"]

    def __init__(self, **kwargs) -> None:
        if "name" in kwargs:
            kwargs["name"] = normalize_string(kwargs["name"])
        super().__init__(**kwargs)

    def __str__(self) -> str:
        return f"{self.name} ({self.serves} persons)"

    @property
    def item_section(self) -> str:
        description_ = [str(self)]
        for item in getattr(self, "items"):
            description_.append(
                f"- {item.quantity} {item.ingredient.unit} {item.ingredient.name}"
            )
        return "\n".join(description_)

    @classmethod
    def create_from_file(cls, path):
        logger.debug(f"loading file: {str(path)!r}")
        name, header, items, instructions = parse_recipe_file(path)
        if Recipe.get_or_none(name=name) is not None:
            logger.info(f"recipe already exist: {name}")
            return
        with DB().atomic():
            recipe = Recipe.create(
                name=name, serves=header["serves"], instructions=instructions
            )
            for quantity, name in items:
                RecipeItem.create_from_tuple(recipe, quantity, name)
        logger.info(f"recipe created: {recipe.name}")
        return recipe

    def add_item(self, item):
        item.recipe = self

    @classmethod
    def exists(cls, name) -> bool:
        return cls.get_or_none(cls.name == name) is not None

    def full(self):
        lines = []
        lines.append(f"serves: {self.serves}")
        lines.append("---")
        for item in self.items:
            lines.append(f"- {item.quantity} {item.ingredient.unit} {item.ingredient}")
        if self.instructions is not None:
            lines.append("---")
            lines.append(self.instructions)

        return "\n".join(lines)

    def rescale(self, servings):
        rescaled = Recipe.create(
            name=f"{self.name} rescaled for {servings}",
            serves=servings,
            instructions=self.instructions,
        )
        for item in self.items:
            RecipeItem.create(
                recipe=rescaled,
                ingredient=item.ingredient,
                quantity=item.quantity * servings / self.serves,
            )
        return rescaled


class RecipeItem(BaseModel):
    """An item of a recipe. Ingredient and Quantity"""

    recipe = peewee.ForeignKeyField(Recipe, backref="items")
    ingredient = peewee.ForeignKeyField(Ingredient)
    quantity = peewee.FloatField()

    def __str__(self) -> str:
        return f"{self.quantity} {self.ingredient.unit} {self.ingredient.name}"

    @classmethod
    def create_from_tuple(cls, recipe, quantity, name) -> Self:
        ingredient, created = Ingredient.get_or_create(
            name=name, unit=str(quantity.unit)
        )
        if created:
            logger.debug(f"new ingredient created: {ingredient}")
        else:
            logger.debug("ingredient found in database")
        item = RecipeItem.create(
            ingredient=ingredient, quantity=quantity.number, recipe=recipe
        )
        logger.debug(f"recipe item created: {item}")
        return item


class Project(BaseModel):
    """Multiple dishes for a certain number of servings"""

    name = peewee.CharField(unique=True)
    servings = peewee.IntegerField()

    def __str__(self) -> str:
        return f"{self.name}: {funcy.ilen(self.recipes)} recipes for {self.servings} servings"

    def __repr__(self) -> str:
        return f"Project(name={self.name},servings={self.servings})"

    @property
    def recipes(self):
        return (dish.recipe for dish in self.dishes)

    @classmethod
    def get_default(cls):
        projects = cls.select()
        match len(projects):
            case 0:
                QueryError("no projects in the database")
            case 1:
                return projects[0]
            case _:
                QueryError(
                    f"{len(projects)} project in the database. could not determine default"
                )

    def shopping_list(self):
        shopping_list = defaultdict(float)
        for recipe in self.recipes:
            for item in recipe.items:
                shopping_list[item.ingredient] += (
                    item.quantity * self.servings / recipe.serves
                )
        return funcy.lmap(tuple, shopping_list.items())

    def priced_shopping_list(self):
        shopping_list = self.shopping_list()
        priced_shopping_list = [
            (
                ingredient,
                quantity,
                ingredient.price * quantity if ingredient.price is not None else None,
            )
            for ingredient, quantity in shopping_list
        ]
        return priced_shopping_list

    def print_summary(self):
        print(self)
        for recipe in self.recipes:
            print(f"- {recipe.name}")

    def print_shopping_list(self):
        t = PrettyTable()
        t.field_names = ["ingredient", "quantity"]

        for ingredient, quantity in self.shopping_list().items():
            t.add_row((ingredient.name, f"{quantity:.1f} {ingredient.unit}"))
        print(t)

    def print_priced_shopping_list(self):
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
    """A dish of a project"""

    project = peewee.ForeignKeyField(Project, backref="dishes")
    recipe = peewee.ForeignKeyField(Recipe)

    def __repr__(self) -> str:
        return f"<ProjectItem({self.recipe} in {self.project})>"


# All model classes
all_models = [Tag, Ingredient, IngredientTag, Recipe, RecipeItem, Project, ProjectItem]
# Entity models
entity_models = [Tag, Ingredient, Recipe, Project]


def create_tables() -> None:
    """Create tables, if they don't exist"""
    logger.debug("creating tables")
    DB().create_tables(all_models)


def reset_tables() -> None:
    """Destructive reset"""
    logger.debug("reseting tables")
    DB().drop_tables(all_models)
    DB().create_tables(all_models)
