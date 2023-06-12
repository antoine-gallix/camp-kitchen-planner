import peewee

db = peewee.SqliteDatabase(":memory:")


class BaseModel(peewee.Model):
    class Meta:
        database = db


class Ingredient(BaseModel):
    name = peewee.CharField(unique=True)

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
