from django.shortcuts import render, redirect
from django.http import HttpResponseRedirect, JsonResponse
from django.contrib.auth.decorators import login_required

# AWS wrapper clients
from aws_lib.dynamodb_client import DynamoDBClient
from aws_lib.sqs_client import SQSClient
from aws_lib.sns_client import SNSClient

from .forms import CreateOrderForm, InventoryForm, RecipeForm

import uuid
import json
import boto3

from aws_config import get_sqs_url, get_sns_topic_arn, AWS_REGION

# CloudKitchen lib logic -- custom library uploaded on pypi
from cloudkitchen_lib.core import (
    max_production,
    consumption_plan,
    deduct_inventory_dict
)


# AWS client initializatoin
ddb = DynamoDBClient()     # DynamoDB wrapper
sqs = SQSClient()          # SQS wrapper
sns = SNSClient()          # SNS wrapper

# S3 for recipe images
S3_BUCKET_NAME = "cloudkitchen-recipes"
s3_client = boto3.client("s3", region_name=AWS_REGION)


# utility helper for sqs and sns
def sqs_queue_url():
    """Retrieve SQS queue URL."""
    url = get_sqs_url()
    if not url:
        raise RuntimeError("SQS queue URL is not configured.")
    return url


def sns_topic_arn():
    """Retrieve SNS topic ARN."""
    arn = get_sns_topic_arn()
    if not arn:
        raise RuntimeError("SNS topic ARN is not configured.")
    return arn


# logic for dashboard view
@login_required
def dashboard(request):
    """
    Loads:
    - All orders
    - Inventory items
    - Recipes for name mapping & simulator dropdown
    - Low-stock alerts (qty < 5)

    Sends data to dashboard page for display.
    """
    orders = ddb.scan("Orders")
    inventory = ddb.scan("Inventory")

    # Map recipe_id → recipe_name for easy readability
    recipes = ddb.scan("Recipes")
    recipe_lookup = {r["recipe_id"]: r["name"] for r in recipes}

    # Attach readable recipe names to orders
    for o in orders:
        o["recipe_name"] = recipe_lookup.get(o.get("recipe"), "Unknown")

    # Detect low stock items
    low_stock = [
        item for item in inventory
        if str(item.get("qty", item.get("quantity", 999999))).isdigit()
        and int(item.get("qty", item.get("quantity", 999999))) < 5
    ]

    return render(request, "dashboard.html", {
        "orders": orders,
        "inventory": inventory,
        "recipes": recipes,     # used by custom lib UI dropdown to select item
        "low_stock": low_stock,
    })


# custom lib usage
@login_required
def simulator_data(request):
    recipe_id = request.GET.get("recipe_id")
    if not recipe_id:
        return JsonResponse({"error": "Missing recipe_id"}, status=400)

    recipe = ddb.get("Recipes", {"recipe_id": recipe_id})
    if not recipe:
        return JsonResponse({"error": "Recipe not found"}, status=404)

    inventory = ddb.scan("Inventory")

    # Library computations
    max_prod = max_production(recipe["ingredients"], inventory)
    plan = consumption_plan(recipe["ingredients"], max_prod)
    inv_after_list = deduct_inventory_dict(inventory, plan)

    # Convert list → dict for UI
    inv_after = {
        it["name"]: it.get("qty", it.get("quantity", 0))
        for it in inv_after_list if it.get("name")
    }

    return JsonResponse({
        "recipe": recipe["ingredients"],
        "max_production": max_prod,
        "inventory_after": inv_after
    })


# order management page view
@login_required
def orders_list(request):
    """
    Shows list of all orders with recipe names.
    """
    orders = ddb.scan("Orders")
    recipe_lookup = {r["recipe_id"]: r["name"] for r in ddb.scan("Recipes")}

    # Attach readable recipe names
    for o in orders:
        o["recipe_name"] = recipe_lookup.get(o.get("recipe"), "Unknown")

    # Optional status filter
    status = request.GET.get("status")
    if status:
        orders = [o for o in orders if o.get("order_status") == status]

    # Optional order_id search filter
    search = request.GET.get("search")
    if search:
        orders = [o for o in orders if search.lower() in o.get("order_id", "").lower()]

    return render(request, "orders_list.html", {
        "orders": orders,
        "status": status,
        "search": search
    })

# creting order and processing order
@login_required
def create_order(request):
    """
    Creates a new order:
    1. Saves to DynamoDB
    2. Sends to SQS for async processing
    """
    if request.method == "POST":
        form = CreateOrderForm(request.POST)
        if form.is_valid():
            order_id = str(uuid.uuid4())
            recipe_id = form.cleaned_data['recipe']

            # Save order to DB
            ddb.put("Orders", {
                "order_id": order_id,
                "recipe": recipe_id,
                "order_status": "PENDING"
            })

            # Push event to SQS
            sqs.send_message(
                sqs_queue_url(),
                json.dumps({"order_id": order_id, "recipe": recipe_id})
            )

            return redirect("orders_list")

    else:
        form = CreateOrderForm()

    return render(request, "create_order.html", {"form": form})


@login_required
def delete_order(request, order_id):
    """Deletes order from DynamoDB."""
    ddb.delete("Orders", {"order_id": order_id})
    return redirect("orders_list")


# inventory page views operations
@login_required
def inventory_list(request):
    """Displays all items."""
    inventory = ddb.scan("Inventory")
    return render(request, "inventory.html", {"inventory": inventory})


@login_required
def add_inventory(request):
    if request.method == "POST":
        form = InventoryForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data["name"]
            qty = form.cleaned_data["qty"]
            item_id = str(uuid.uuid4())

            ddb.put("Inventory", {"item_id": item_id, "name": name, "qty": qty})

            # Send low stock alert
            if qty < 5:
                sns.publish(sns_topic_arn(), f"Low stock alert: {name} has qty {qty}")

            return redirect("inventory_list")

    else:
        form = InventoryForm()

    return render(request, "add_inventory.html", {"form": form})


@login_required
def edit_inventory(request, item_id): # edit all the items listed in the inventory
    item = ddb.get("Inventory", {"item_id": item_id})
    if not item:
        return redirect("inventory_list")

    if request.method == "POST":
        form = InventoryForm(request.POST)
        if form.is_valid():
            qty = form.cleaned_data["qty"]

            ddb.put("Inventory", {
                "item_id": item_id,
                "name": item["name"],   # Name is immutable, cannot be changes as we can only change the qty
                "qty": qty
            })

            return redirect("inventory_list")

    else:
        # Pre-fill form with existing values
        form = InventoryForm(initial={
            "name": item["name"],
            "qty": item["qty"]
        })

    return render(request, "edit_inventory.html", {"form": form, "item": item})


@login_required
def delete_inventory(request, item_id):
    """Removes an item from inventory."""
    ddb.delete("Inventory", {"item_id": item_id})
    return redirect("inventory_list")


# all the recipe operations
@login_required
def recipe_list(request):
    """Shows all recipes."""
    recipes = ddb.scan("Recipes")
    return render(request, "recipes.html", {"recipes": recipes})


@login_required
def add_recipe(request):
    """
    Adds a new recipe.
    Uploads optional image to S3.
    """
    if request.method == "POST":
        form = RecipeForm(request.POST, request.FILES)
        if form.is_valid():
            recipe_id = str(uuid.uuid4())
            name = form.cleaned_data['name']
            ingredients = form.cleaned_data['ingredients']
            image_file = request.FILES.get('image')

            # Upload image to S3
            s3_key = None
            if image_file:
                s3_key = f"recipes/{recipe_id}/{image_file.name}"
                s3_client.put_object(
                    Bucket=S3_BUCKET_NAME,
                    Key=s3_key,
                    Body=image_file,
                    ContentType=image_file.content_type
                )

            # Save recipe to DB
            ddb.put("Recipes", {
                "recipe_id": recipe_id,
                "name": name,
                "ingredients": ingredients,
                "s3_key": s3_key
            })

            return redirect("recipe_list")

    else:
        form = RecipeForm()

    return render(request, "add_recipe.html", {"form": form})


@login_required
def edit_recipe(request, recipe_id):
    """
    Edit a recipe including S3 image re-upload.
    """
    recipe = ddb.get("Recipes", {"recipe_id": recipe_id})

    if request.method == "POST":
        form = RecipeForm(request.POST, request.FILES)
        if form.is_valid():
            name = form.cleaned_data["name"]
            ingredients = form.cleaned_data["ingredients"]
            image_file = request.FILES.get('image')

            s3_key = recipe.get("s3_key")

            # Replace image if a new one is uploaded
            if image_file:
                s3_key = f"recipes/{recipe_id}/{image_file.name}"
                s3_client.put_object(
                    Bucket=S3_BUCKET_NAME,
                    Key=s3_key,
                    Body=image_file,
                    ContentType=image_file.content_type
                )

            ddb.put("Recipes", {
                "recipe_id": recipe_id,
                "name": name,
                "ingredients": ingredients,
                "s3_key": s3_key
            })

            return redirect("recipe_list")

    else:
        # Populate form with readable string ingredients
        ingredients_text = ",".join(f"{k}:{v}" for k, v in recipe["ingredients"].items())
        form = RecipeForm(initial={
            "name": recipe["name"],
            "ingredients": ingredients_text
        })

    return render(request, "edit_recipe.html", {"form": form, "recipe": recipe})


@login_required
def delete_recipe(request, recipe_id):
    """Delete recipe from DynamoDB."""
    ddb.delete("Recipes", {"recipe_id": recipe_id})
    return redirect("recipe_list")


@login_required
def download_recipe_file(request, recipe_id):
    """
    Generates a temporary (presigned) URL so the user can download
    the recipe image stored in S3.
    """
    recipe = ddb.get("Recipes", {"recipe_id": recipe_id})
    if not recipe or not recipe.get("s3_key"):
        return redirect("recipe_list")

    presigned_url = s3_client.generate_presigned_url(
        "get_object",
        Params={"Bucket": S3_BUCKET_NAME, "Key": recipe['s3_key']},
        ExpiresIn=300
    )
    return redirect(presigned_url)
