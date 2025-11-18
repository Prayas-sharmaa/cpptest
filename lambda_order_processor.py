import json
import boto3
from decimal import Decimal

dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
inventory_table = dynamodb.Table("Inventory")
recipes_table = dynamodb.Table("Recipes")
orders_table = dynamodb.Table("Orders")
sns = boto3.client("sns")


def lambda_handler(event, context):
    print("[Event]", event)

    for record in event.get("Records", []):
        body = json.loads(record["body"])
        order_id = body["order_id"]
        recipe_id = body["recipe"]

        try:
            deduct_inventory(recipe_id)
            update_order_status(order_id, "COMPLETED")
        except Exception as e:
            print("[ERROR]", str(e))
            update_order_status(order_id, "FAILED")

    return {"statusCode": 200, "body": "Done"}


def deduct_inventory(recipe_id):
    recipe = recipes_table.get_item(Key={"recipe_id": recipe_id}).get("Item")
    if not recipe:
        raise ValueError("Recipe not found")

    ingredients = recipe.get("ingredients", {})

    for item_id, qty_needed in ingredients.items():

        inv = inventory_table.get_item(Key={"item_id": item_id}).get("Item")
        if not inv:
            raise ValueError(f"Missing inventory: {item_id}")

        current_qty = int(inv["qty"])
        new_qty = current_qty - int(qty_needed)

        if new_qty < 0:
            raise ValueError(f"Insufficient inventory for {item_id}")

        inventory_table.update_item(
            Key={"item_id": item_id},
            UpdateExpression="SET qty = :q",
            ExpressionAttributeValues={":q": Decimal(new_qty)}
        )

        if new_qty < 5:
            sns.publish(
                TopicArn=get_sns_topic_arn(),
                Subject="Low Stock Alert",
                Message=f"{item_id} low: {new_qty}"
            )


def update_order_status(order_id, status):
    orders_table.update_item(
        Key={"order_id": order_id},
        UpdateExpression="SET order_status = :s",
        ExpressionAttributeValues={":s": status}
    )
