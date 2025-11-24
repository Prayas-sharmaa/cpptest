from django import forms
from aws_lib.dynamodb_client import DynamoDBClient

ddb = DynamoDBClient()


class CreateOrderForm(forms.Form):
    recipe = forms.ChoiceField(choices=[], label="Select Recipe")
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        recipes = ddb.scan("Recipes")
        self.fields['recipe'].choices = [
            (r["recipe_id"], r.get("name", r["recipe_id"])) for r in recipes
        ]


class InventoryForm(forms.Form):
    name = forms.CharField(max_length=255)
    qty = forms.IntegerField(min_value=0)

    def __init__(self, *args, **kwargs):
        """
        If editing, disable the name field (readonly).
        """
        super().__init__(*args, **kwargs)

        if "initial" in kwargs and kwargs["initial"].get("name"):
            self.fields["name"].widget.attrs["readonly"] = True


class RecipeForm(forms.Form):
    name = forms.CharField(max_length=100)
    ingredients = forms.CharField(
        max_length=500,
        help_text="Format: item1:qty1,item2:qty2"
    )
    image = forms.ImageField(required=False)

    def clean_ingredients(self):
        raw = self.cleaned_data["ingredients"].strip()
        ingredients = {}

        if not raw:
            raise forms.ValidationError("Ingredients cannot be empty.")

        for entry in raw.split(","):
            if ":" not in entry:
                raise forms.ValidationError(f"Invalid ingredient format: '{entry}'")
            key, value = entry.split(":")
            key, value = key.strip(), value.strip()
            if not key or not value.isdigit():
                raise forms.ValidationError(f"Invalid entry: {entry}")
            ingredients[key] = int(value)

        return ingredients
