import json
from decimal import Decimal
import boto3

# --------------------------
# AWS Config / Hardcoded
# --------------------------
AWS_REGION = "us-east-1"

# DynamoDB tables
ORDERS_TABLE = "Orders"
INVENTORY_TABLE = "Inventory"
RECIPES_TABLE = "Recipes"

# SNS topic ARN for low-stock alerts
SNS_TOPIC_ARN = "arn:aws:sns:us-east-1:326603068904:cloudkitchen-order-notifications"

# AWS Clients
dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)
sqs = boto3.client("sqs", region_name=AWS_REGION)
sns = boto3.client("sns", region_name=AWS_REGION)

orders_table = dynamodb.Table(ORDERS_TABLE)
inventory_table = dynamodb.Table(INVENTORY_TABLE)
recipes_table = dynamodb.Table(RECIPES_TABLE)

# --------------------------
# Helper to safely convert DynamoDB Decimal
# --------------------------
def to_int(value):
    if isinstance(value, Decimal):
        return int(value)
    return value

# --------------------------
# Lambda Handler
# --------------------------
def lambda_handler(event, context):
    print("Received event:", json.dumps(event))
    
    for record in event.get("Records", []):
        try:
            body = json.loads(record["body"])
            order_id = body.get("order_id")
            recipe_id = body.get("recipe")
            if not order_id or not recipe_id:
                print("Missing order_id or recipe_id in message.")
                continue

            # Fetch recipe
            recipe_resp = recipes_table.get_item(Key={"recipe_id": recipe_id})
            recipe = recipe_resp.get("Item")
            if not recipe:
                print(f"Recipe {recipe_id} not found. Marking order failed.")
                orders_table.update_item(
                    Key={"order_id": order_id},
                    UpdateExpression="SET order_status = :s",
                    ExpressionAttributeValues={":s": "FAILED"}
                )
                continue

            # Check inventory
            success = True
            for item_name, qty_needed in recipe["ingredients"].items():
                inv_items = [i for i in inventory_table.scan()['Items'] if i['name'] == item_name]
                if not inv_items:
                    success = False
                    print(f"Inventory item {item_name} not found.")
                    break

                inv_item = inv_items[0]
                current_qty = to_int(inv_item.get("qty", 0))
                if current_qty < qty_needed:
                    success = False
                    print(f"Not enough {item_name}. Needed {qty_needed}, available {current_qty}")
                    break

            # Deduct inventory if available
            if success:
                for item_name, qty_needed in recipe["ingredients"].items():
                    inv_items = [i for i in inventory_table.scan()['Items'] if i['name'] == item_name]
                    inv_item = inv_items[0]
                    new_qty = to_int(inv_item.get("qty", 0)) - qty_needed

                    inventory_table.update_item(
                        Key={"item_id": inv_item['item_id']},
                        UpdateExpression="SET qty = :q",
                        ExpressionAttributeValues={":q": Decimal(new_qty)}
                    )

                    # Low stock SNS alert
                    if new_qty < 5:
                        sns.publish(
                            TopicArn=SNS_TOPIC_ARN,
                            Message=f"Low stock alert: {item_name} has qty {new_qty}"
                        )

                orders_table.update_item(
                    Key={"order_id": order_id},
                    UpdateExpression="SET order_status = :s",
                    ExpressionAttributeValues={":s": "COMPLETED"}
                )
                print(f"Order {order_id} completed successfully.")
            else:
                orders_table.update_item(
                    Key={"order_id": order_id},
                    UpdateExpression="SET order_status = :s",
                    ExpressionAttributeValues={":s": "FAILED"}
                )
                print(f"Order {order_id} failed due to insufficient inventory.")

        except Exception as e:
            print(f"Error processing record: {e}")
            if "order_id" in locals():
                orders_table.update_item(
                    Key={"order_id": order_id},
                    UpdateExpression="SET order_status = :s",
                    ExpressionAttributeValues={":s": "FAILED"}
                )

    return {"statusCode": 200, "body": json.dumps("Processed all messages.")}
