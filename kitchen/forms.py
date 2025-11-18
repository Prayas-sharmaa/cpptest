from django import forms
from aws_lib.dynamodb_client import DynamoDBClient

ddb = DynamoDBClient()


# -----------------------------
# Create Order Form
# -----------------------------
class CreateOrderForm(forms.Form):
    recipe = forms.ChoiceField(choices=[], label="Select Recipe")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Load recipes from DynamoDB
        recipes = ddb.scan("Recipes")

        # Populate dropdown
        self.fields['recipe'].choices = [
            (r["recipe_id"], r.get("name", r["recipe_id"])) for r in recipes
        ]


# -----------------------------
# Inventory Form
# -----------------------------
class InventoryForm(forms.Form):
    name = forms.CharField(max_length=255)
    qty = forms.IntegerField(min_value=0)


# -----------------------------
# Recipe Form (Updated)
# -----------------------------
class RecipeForm(forms.Form):
    name = forms.CharField(max_length=100)
    ingredients = forms.CharField(
        max_length=500,
        help_text="Format: item1:qty1,item2:qty2"
    )
    image = forms.ImageField(required=False)

    def clean_ingredients(self):
        """
        Convert input text:
        milk:2,sugar:3 → {"milk": 2, "sugar": 3}
        and validate everything.
        """
        raw = self.cleaned_data["ingredients"].strip()
        ingredients = {}

        if not raw:
            raise forms.ValidationError("Ingredients cannot be empty.")

        parts = raw.split(",")

        for entry in parts:
            if ":" not in entry:
                raise forms.ValidationError(
                    f"Invalid ingredient format: '{entry}'. Expected item:qty"
                )

            key, value = entry.split(":")

            key = key.strip()
            value = value.strip()

            if not key:
                raise forms.ValidationError("Ingredient name cannot be empty.")

            if not value.isdigit():
                raise forms.ValidationError(
                    f"Quantity must be a number. Found '{value}' in '{entry}'."
                )

            ingredients[key] = int(value)

        return ingredients
