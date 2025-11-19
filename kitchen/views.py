from django.shortcuts import render, redirect
from aws_lib.dynamodb_client import DynamoDBClient
from aws_lib.sqs_client import SQSClient
from aws_lib.sns_client import SNSClient
from .forms import CreateOrderForm, InventoryForm, RecipeForm
import uuid, json

ddb = DynamoDBClient()
sqs = SQSClient()
sns = SNSClient()

from aws_config import get_sqs_url, get_sns_topic_arn

# ----------------------
# Lazy AWS property functions
# ----------------------

def sqs_queue_url():
    """Return the SQS queue URL at runtime (never during import)."""
    url = get_sqs_url()
    if not url:
        raise RuntimeError("SQS queue URL is not configured. Set SQS_QUEUE_NAME.")
    return url

def sns_topic_arn():
    """Return the SNS topic ARN at runtime (never during import)."""
    arn = get_sns_topic_arn()
    if not arn:
        raise RuntimeError("SNS topic ARN is not configured. Set SNS_TOPIC_ARN.")
    return arn

# ----------------------
# Dashboard
# ----------------------
def dashboard(request):
    orders = ddb.scan("Orders")
    inventory = ddb.scan("Inventory")

    # Safe low_stock calculation
    low_stock = [item for item in inventory
                 if str(item.get("qty", item.get("quantity", 999999))).isdigit() and int(item.get("qty", item.get("quantity", 999999))) < 5]

    orders_pending = len([o for o in orders if o.get('order_status') == "PENDING"])
    orders_completed = len([o for o in orders if o.get('order_status') == "COMPLETED"])
    orders_failed = len([o for o in orders if o.get('order_status') == "FAILED"])

    return render(request, "dashboard.html", {
        "orders": orders,
        "inventory": inventory,
        "low_stock": low_stock,
        "orders_pending": orders_pending,
        "orders_completed": orders_completed,
        "orders_failed": orders_failed
    })

# ----------------------
# Orders
# ----------------------
def orders_list(request):
    orders = ddb.scan("Orders")
    recipe_lookup = {r["recipe_id"]: r["name"] for r in ddb.scan("Recipes")}

    for o in orders:
        o["recipe_name"] = recipe_lookup.get(o.get("recipe"), "Unknown")

    status = request.GET.get("status")
    if status:
        orders = [o for o in orders if o.get("order_status") == status]

    search = request.GET.get("search")
    if search:
        orders = [o for o in orders if search.lower() in o.get("order_id", "").lower()]

    return render(request, "orders_list.html", {
        "orders": orders,
        "status": status,
        "search": search
    })

def create_order(request):
    if request.method == "POST":
        form = CreateOrderForm(request.POST)
        if form.is_valid():
            order_id = str(uuid.uuid4())
            recipe_id = form.cleaned_data['recipe']

            ddb.put("Orders", {
                "order_id": order_id,
                "recipe": recipe_id,
                "order_status": "PENDING"
            })

            sqs.send_message(
                sqs_queue_url(),
                json.dumps({"order_id": order_id, "recipe": recipe_id})
            )

            return redirect("orders_list")
    else:
        form = CreateOrderForm()
    return render(request, "create_order.html", {"form": form})

def delete_order(request, order_id):
    ddb.delete("Orders", {"order_id": order_id})
    return redirect("orders_list")

# ----------------------
# Inventory
# ----------------------
def inventory_list(request):
    inventory = ddb.scan("Inventory")
    return render(request, "inventory.html", {"inventory": inventory})

def add_inventory(request):
    if request.method == "POST":
        form = InventoryForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data["name"]
            qty = form.cleaned_data["qty"]

            item_id = str(uuid.uuid4())
            ddb.put("Inventory", {"item_id": item_id, "name": name, "qty": qty})

            if qty < 5:
                sns.publish(sns_topic_arn(), f"Low stock alert: {name} has qty {qty}")

            return redirect("inventory_list")
    else:
        form = InventoryForm()
    return render(request, "add_inventory.html", {"form": form})

def edit_inventory(request, item_id):
    item = ddb.get("Inventory", {"item_id": item_id})

    if request.method == "POST":
        name = request.POST["name"]
        qty = int(request.POST["qty"])

        ddb.put("Inventory", {"item_id": item_id, "name": name, "qty": qty})
        return redirect("inventory_list")

    return render(request, "edit_inventory.html", {"item": item})

def delete_inventory(request, item_id):
    ddb.delete("Inventory", {"item_id": item_id})
    return redirect("inventory_list")

# ----------------------
# Recipes
# ----------------------
def recipe_list(request):
    recipes = ddb.scan("Recipes")
    return render(request, "recipes.html", {"recipes": recipes})

def add_recipe(request):
    if request.method == "POST":
        form = RecipeForm(request.POST, request.FILES)
        if form.is_valid():
            recipe_id = str(uuid.uuid4())
            name = form.cleaned_data['name']
            ingredients = form.cleaned_data['ingredients']  # Already a dict

            ddb.put("Recipes", {
                "recipe_id": recipe_id,
                "name": name,
                "ingredients": ingredients
            })

            return redirect("recipe_list")
    else:
        form = RecipeForm()

    return render(request, "add_recipe.html", {"form": form})


def edit_recipe(request, recipe_id):
    recipe = ddb.get("Recipes", {"recipe_id": recipe_id})

    if request.method == "POST":
        form = RecipeForm(request.POST, request.FILES)
        if form.is_valid():
            name = form.cleaned_data["name"]
            ingredients = form.cleaned_data["ingredients"]  # Already a dict

            ddb.put("Recipes", {
                "recipe_id": recipe_id,
                "name": name,
                "ingredients": ingredients
            })

            return redirect("recipe_list")
    else:
        # Convert ingredients dict to string for textarea
        ingredients_text = ",".join(f"{k}:{v}" for k, v in recipe["ingredients"].items())
        form = RecipeForm(initial={"name": recipe["name"], "ingredients": ingredients_text})

    return render(request, "edit_recipe.html", {"form": form, "recipe": recipe})


def delete_recipe(request, recipe_id):
    ddb.delete("Recipes", {"recipe_id": recipe_id})
    return redirect("recipe_list")
