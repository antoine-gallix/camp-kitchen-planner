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
    unit = peewee.CharField(unique=True, default=None)

    def __str__(self):
        return str(self.name)

    def __repr__(self):
        return f"<Ingredient({self})>"


class Recipe(BaseModel):
    name = peewee.CharField(unique=True)

    def __str__(self):
        return str(self.name)

    def __repr__(self):
        return f"<Recipe({self.name})>"

    @property
    def description(self):
        description_ = [str(self)]
        for item in getattr(self, "items"):
            description_.append(f"- {item.quantity} x {item.ingredient.name}")
        return "\n".join(description_)


class Item(BaseModel):
    recipe = peewee.ForeignKeyField(Recipe, backref="items")
    ingredient = peewee.ForeignKeyField(Ingredient)
    quantity = peewee.IntegerField()


all_models = [Ingredient, Recipe, Item]


def create_tables():
    print("creating tables")
    db.create_tables(all_models)


def reset_tables():
    print("reseting tables")
    db.drop_tables(all_models)
    db.create_tables(all_models)
