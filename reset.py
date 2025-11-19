import boto3, os, json
from aws_config import dynamodb_resource, sqs_client

# -------------------------------
# 1️⃣ Setup AWS clients
# -------------------------------
ddb = dynamodb_resource()
sqs = sqs_client()

queue_name = os.getenv("SQS_ORDER_QUEUE_NAME", "cloudkitchen-orders")
queue_url = sqs.get_queue_url(QueueName=queue_name)['QueueUrl']

# DynamoDB table names to reset (skip KitchenOrders)
tables = ["Orders", "Recipes", "Inventory"]

# -------------------------------
# 2️⃣ Clear DynamoDB tables safely
# -------------------------------
for table_name in tables:
    table = ddb.Table(table_name)
    print(f"Clearing table: {table_name}")

    # Get primary key names dynamically
    key_names = [k['AttributeName'] for k in table.key_schema]

    # Scan all items
    response = table.scan()
    items = response.get("Items", [])

    # Delete items using correct key(s)
    with table.batch_writer() as batch:
        for item in items:
            key = {k: item[k] for k in key_names}
            batch.delete_item(Key=key)
    print(f"✅ Cleared {len(items)} items from {table_name}")

# -------------------------------
# 3️⃣ Clear SQS queue
# -------------------------------
print(f"Clearing SQS queue: {queue_name}")
while True:
    msgs = sqs.receive_message(QueueUrl=queue_url, MaxNumberOfMessages=10)
    if 'Messages' not in msgs:
        break
    for m in msgs['Messages']:
        sqs.delete_message(QueueUrl=queue_url, ReceiptHandle=m['ReceiptHandle'])
print("✅ SQS queue cleared")

# -------------------------------
# 4️⃣ Insert test recipe
# -------------------------------
recipes_table = ddb.Table("Recipes")
test_recipe = {
    "recipe_id": "recipe1",
    "recipe_name": "Test Recipe",
    "ingredients": ["tomato", "cheese", "dough"]
}
recipes_table.put_item(Item=test_recipe)
print("✅ Test recipe inserted")

# -------------------------------
# 5️⃣ Insert inventory items (using correct primary key)
# -------------------------------
inventory_table = ddb.Table("Inventory")

# Check table key schema dynamically
key_names = [k['AttributeName'] for k in inventory_table.key_schema]

for ingredient in test_recipe["ingredients"]:
    item = {key_names[0]: ingredient, "quantity": 100}  # assign ingredient to primary key
    inventory_table.put_item(Item=item)

print("✅ Inventory items inserted")


# -------------------------------
# 6️⃣ Insert test order
# -------------------------------
orders_table = ddb.Table("Orders")
test_order = {
    "order_id": "test123",
    "recipe_id": "recipe1",
    "order_status": "PENDING"
}
orders_table.put_item(Item=test_order)
print("✅ Test order inserted into Orders table")

# -------------------------------
# 7️⃣ Send test order to SQS
# -------------------------------
sqs.send_message(QueueUrl=queue_url, MessageBody=json.dumps(test_order))
print(f"✅ Test order sent to SQS: {queue_name}")
