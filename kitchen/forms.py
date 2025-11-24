from django import forms
from aws_lib.dynamodb_client import DynamoDBClient

# Initialize DynamoDB client
ddb = DynamoDBClient()


class CreateOrderForm(forms.Form):
    """
    Form used to create a new order.
    """
    recipe = forms.ChoiceField(choices=[], label="Select Recipe")

    def __init__(self, *args, **kwargs):
        """
        On initialization, fetch all recipes and populate the dropdown.
        """
        super().__init__(*args, **kwargs)

        # Load all recipes
        recipes = ddb.scan("Recipes")

        # Populate choices (value = recipe_id, display = recipe name)
        self.fields['recipe'].choices = [
            (r["recipe_id"], r.get("name", r["recipe_id"]))
            for r in recipes
        ]


class InventoryForm(forms.Form):
    """
    Form used for adding or editing inventory items.
    """
    name = forms.CharField(max_length=255)
    qty = forms.IntegerField(min_value=0)

    def __init__(self, *args, **kwargs):
        """
        Override form initialization.
        """
        super().__init__(*args, **kwargs)

        # When editing, disable editing of item "name"
        if "initial" in kwargs and kwargs["initial"].get("name"):
            self.fields["name"].widget.attrs["readonly"] = True


class RecipeForm(forms.Form):
    """
    Form used for creating or editing a recipe.
    """
    name = forms.CharField(max_length=100)

    ingredients = forms.CharField(
        max_length=500,
        help_text="Format: item1:qty1,item2:qty2"
    )

    # Optional image upload (stored on S3)
    image = forms.ImageField(required=False)

    def clean_ingredients(self):
        """
        Custom validation for the ingredients field.
        """
        raw = self.cleaned_data["ingredients"].strip()
        ingredients = {}

        if not raw:
            raise forms.ValidationError("Ingredients cannot be empty.")

        # Parse each "item:qty" pair
        for entry in raw.split(","):
            if ":" not in entry:
                raise forms.ValidationError(
                    f"Invalid ingredient format: '{entry}'. Use item:qty"
                )

            key, value = entry.split(":")
            key, value = key.strip(), value.strip()

            # Validate both item name and qty
            if not key or not value.isdigit():
                raise forms.ValidationError(f"Invalid entry: {entry}")

            ingredients[key] = int(value)

        return ingredients
