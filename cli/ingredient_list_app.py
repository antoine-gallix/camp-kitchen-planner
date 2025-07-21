from textual.app import App, ComposeResult
from textual.widgets import DataTable, Header, Footer, Input, Static
from textual.containers import Container


class IngredientsVisualizer(App):
    """A simple TUI app to display ingredients in a table."""

    CSS_PATH = """./app.tcss"""

    def __init__(self, ingredients):
        super().__init__()
        self.ingredients = ingredients

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header()
        yield Static(id="count-display")
        yield Input(placeholder="name", id="filter-input")
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

        self.update_table("")

    def update_table(self, filter_text: str) -> None:
        """Update table content based on filter."""
        table = self.query_one("#ingredients-table", DataTable)

        # Clear existing rows
        table.clear()

        # Filter ingredients by name (case-insensitive)
        filtered_ingredients = [
            ingredient
            for ingredient in self.ingredients
            if filter_text.lower() in ingredient.name.lower()
        ]

        # Add filtered rows
        for ingredient in filtered_ingredients:
            table.add_row(ingredient.name, ingredient.unit)

        # Update count display
        count_display = self.query_one("#count-display")

        total_count = len(self.ingredients)
        filtered_count = len(filtered_ingredients)

        if filter_text:
            count_display.update(f"{filtered_count}/{total_count} ingredients")
        else:
            count_display.update(f"{total_count} ingredients")

    def on_input_changed(self, event: Input.Changed) -> None:
        """Handle input changes for filtering."""
        if event.input.id == "filter-input":
            self.update_table(event.value)
