from collections import defaultdict
from typing import Self

import funcy
import peewee
from prettytable import PrettyTable
from rich import print
from rich.console import Group
from rich.panel import Panel
from rich.text import Text

from planner import logger
from planner.database import DB
from planner.errors import QueryError
from planner.logging import add_file_sink
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
        try:
            IngredientTag.create(ingredient=self, tag=tag)
        except peewee.IntegrityError:
            logger.warning(f"tag already existed on {self.name}: {tag.name}")

    @property
    def tags(self):
        return list(
            Tag.select()
            .join(IngredientTag)
            .join(Ingredient)
            .where(Ingredient.id == self.id)
        )

    @property
    def category(self):
        tag_names = [tag.name for tag in self.tags]
        if "uncommon" in tag_names:
            return "uncommon"
        elif "fresh" in tag_names:
            return "fresh"
        else:
            return "usual"

    def dump(self) -> dict:
        dump_ = dict(
            name=self.name, unit=str(self.unit), tags=[str(tag) for tag in self.tags]
        )
        if self.price is not None:
            dump_["price"] = self.price
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

    def add_item(self, quantity, name) -> Self:
        ingredient, created = Ingredient.get_or_create(
            name=name, unit=str(quantity.unit)
        )
        if created:
            logger.debug(f"new ingredient created: {ingredient}")
        else:
            logger.debug("ingredient found in database")
        item = RecipeItem.create(
            ingredient=ingredient, quantity=quantity.number, recipe=self
        )
        logger.debug(f"recipe item created: {item}")
        return item

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
                recipe.add_item(quantity, name)
        logger.info(f"recipe created: {recipe.name}")
        return recipe

    @classmethod
    def exists(cls, name) -> bool:
        return cls.get_or_none(cls.name == name) is not None

    @funcy.joining("\n")
    def as_text(self, servings=None):
        if servings is not None:
            scaling_factor = servings / self.serves
        else:
            scaling_factor = 1
        yield f"serves: {self.serves * scaling_factor}"
        yield "---"
        for item in self.items:
            yield f"- {item.quantity * scaling_factor:.3f} {item.ingredient.unit} {item.ingredient}"
        if self.instructions is not None:
            yield "---"
            yield self.instructions


class IngredientQuantity(BaseModel):
    """An item of a recipe. Ingredient and Quantity"""

    ingredient = peewee.ForeignKeyField(Ingredient)
    quantity = peewee.FloatField()

    def __str__(self) -> str:
        return f"{self.quantity} {self.ingredient.unit} {self.ingredient.name}"


class RecipeItem(IngredientQuantity):
    """An item of a recipe. Ingredient and Quantity"""

    recipe = peewee.ForeignKeyField(Recipe, backref="items")


class Project(BaseModel):
    """Multiple dishes for a certain number of servings"""

    name = peewee.CharField(unique=True)

    _list_fields = ["id", "name", ("items", len)]

    def __str__(self) -> str:
        return f"{self.name}: {funcy.ilen(self.items)} recipes"

    def __repr__(self) -> str:
        return f"Project(name={self.name})"

    @classmethod
    def get_default(cls):
        projects = cls.select()
        match len(projects):
            case 0:
                QueryError("no projects in the database")
            case 1:
                return projects[0]
            case _:
                raise QueryError(
                    f"{len(projects)} project in the database. could not determine default"
                )

    def add_recipe(self, recipe, servings):
        ProjectRecipe.create(project=self, recipe=recipe, servings=servings)

    # --- compute shopping list

    def shopping_list(self):
        shopping_list = defaultdict(float)
        items_before_aggregation = 0
        for project_recipe in self.items:
            scaling_factor = project_recipe.servings / project_recipe.recipe.serves
            logger.debug(
                f"========  {project_recipe.recipe} scaled from {project_recipe.recipe.serves} to {project_recipe.servings} (x{scaling_factor:.2f}). {len(project_recipe.recipe.items)} items"
            )
            for ingredient_quantity in project_recipe.recipe.items:
                items_before_aggregation += 1
                scaled_quantity = ingredient_quantity.quantity * scaling_factor
                logger.debug(
                    f"{ingredient_quantity.ingredient.name}: {scaled_quantity:.2f} {ingredient_quantity.ingredient.unit}"
                )
                shopping_list[ingredient_quantity.ingredient] += scaled_quantity
        logger.info(
            f"aggregation reduced item list from {items_before_aggregation} to {len(shopping_list)}"
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

    # --- prints

    def detail_printable(self):
        return Panel(
            Group(
                *(
                    Text(f"- {item.recipe.name!r} for {item.servings} persons")
                    for item in self.items
                )
            ),
            title=f"Project: {self.name!r}",
            expand=False,
        )

    def shopping_list_table(self):
        table = PrettyTable()
        table.field_names = ["ingredient", "quantity", "category"]
        rows = [
            (
                ingredient.name,
                f"{quantity:.1f} {ingredient.unit}",
                ingredient.category,
            )
            for ingredient, quantity in self.shopping_list()
        ]
        rows = sorted(rows, key=lambda r: (r[2], r[0]))
        for row in rows:
            table.add_row(row)
        return table

    def priced_shopping_list_table(self):
        table = PrettyTable()
        table.field_names = [
            "ingredient",
            "quantity",
            "price",
        ]

        for ingredient, quantity, price in self.priced_shopping_list():
            if price is not None:
                price_str = f"({price} euros)"
            else:
                price_str = f"(no price data)"
            table.add_row(
                (ingredient.name, f"{quantity:.1f} {ingredient.unit}", price_str)
            )
        return table

    def csv_shopping_list(self):
        file_sink = add_file_sink()
        t = PrettyTable()

        t.field_names = ["ingredient", "quantity", "unit", "category"]
        rows = [
            (
                ingredient.name,
                f"{quantity:.1f}",
                str(ingredient.unit),
                ingredient.category,
            )
            for ingredient, quantity in self.shopping_list()
        ]
        rows = sorted(rows, key=lambda r: (r[3], r[0]))
        for row in rows:
            t.add_row(row)
        logger.remove(file_sink)
        return t.get_csv_string()

    def compute(self): ...


class ProjectRecipe(BaseModel):
    """A dish of a project"""

    project = peewee.ForeignKeyField(Project, backref="items")
    recipe = peewee.ForeignKeyField(Recipe)
    servings = peewee.IntegerField()

    def __repr__(self) -> str:
        return f"<ProjectItem(project={self.project!r},recipe={self.recipe!r},servings={self.servings})>"


class ShoppingList(BaseModel):
    """List of ingredients and quantities."""

    name = peewee.CharField(unique=True)


# All model classes
all_models = [
    Tag,
    Ingredient,
    IngredientTag,
    Recipe,
    RecipeItem,
    Project,
    ProjectRecipe,
]
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
