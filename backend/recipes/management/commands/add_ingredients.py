import json
from django.core.management import BaseCommand
from recipes.models import Ingredient

JSON_FILE_PATH = './data/ingredients.json'


class Command(BaseCommand):
    help = """
        Loads data from JSON 'file'.
        If something goes wrong when you load data from the JSON file,
        first delete the db.sqlite3 file to destroy the database.
        Then, run `python manage.py migrate` for a new empty
        database with tables.
        """

    def load_ingredients_data(self):
        with open(JSON_FILE_PATH, 'r', encoding='utf-8') as json_file:
            data = json.load(json_file)
            for item in data:
                Ingredient.objects.get_or_create(
                    name=item['name'], measurement_unit=item['measurement_unit']
                )

    def handle(self, *args, **options):
        self.load_ingredients_data()
        self.stdout.write(self.style.SUCCESS('Data was loaded successfully.'))
