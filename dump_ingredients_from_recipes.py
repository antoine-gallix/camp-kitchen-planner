import planner.loader
import planner.models

planner.models.create_tables()
planner.loader.load_recipe_dir("recipes/")
planner.loader.dump_ingredients("ingredients.yaml")
