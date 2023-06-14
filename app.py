from textual.app import App
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Button, Header, Label, Static

import models


def view_recipes():
    yield from (recipe.description for recipe in models.Recipe.select())


class MyApp(App):
    TITLE = "Camp Kitchen Planner"
    CSS_PATH = "style.css"

    def compose(self):
        yield Header()
        yield Horizontal(
            Vertical(
                Button("List recipes", id="list_recipes"),
                Button("Create recipes", id="create_recipes"),
                classes="panel",
                id="left_panel",
            ),
            Vertical(
                Label("Recipes"),
                Label("\n".join(view_recipes()), id="recipes"),
                classes="panel",
                id="right_panel",
            ),
        )


if __name__ == "__main__":
    app = MyApp()
    app.run()
