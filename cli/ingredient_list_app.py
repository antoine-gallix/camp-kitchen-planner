from textual.app import App, ComposeResult
from textual.widgets import DataTable, Header, Footer
from textual.containers import Container


class IngredientsVisualizer(App):
    """A simple TUI app to display ingredients in a table."""

    CSS = """
    DataTable {
        height: 1fr;
    }
    
    Container {
        padding: 1;
    }
    """

    def __init__(self, ingredients):
        super().__init__()
        self.ingredients = ingredients

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header()
        with Container():
            yield DataTable(id="ingredients-table")
        yield Footer()

    def on_mount(self) -> None:
        """Called when app starts."""
        table = self.query_one("#ingredients-table", DataTable)

        # Add columns
        table.add_columns("Name", "Unit")

        # Configure table for row-by-row navigation
        table.cursor_type = "row"

        # Add rows from ingredients data
        for ingredient in self.ingredients:
            table.add_row(ingredient.name, ingredient.unit)
