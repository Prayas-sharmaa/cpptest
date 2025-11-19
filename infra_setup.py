# infra_setup.py
import os
from aws_config import dynamodb_resource, sqs_client, sns_client

# Get environment variables
ORDERS_TABLE = os.getenv("DDB_ORDERS_TABLE", "Orders")
INVENTORY_TABLE = os.getenv("DDB_INVENTORY_TABLE", "Inventory")
RECIPES_TABLE = os.getenv("DDB_RECIPES_TABLE", "Recipes")
QUEUE_NAME = os.getenv("SQS_ORDER_QUEUE_NAME", "cloudkitchen-orders")
SNS_TOPIC_NAME = os.getenv("SNS_ORDER_TOPIC_NAME", "cloudkitchen-order-notifications")

# Initialize AWS clients/resources
ddb = dynamodb_resource()
sqs = sqs_client()
sns = sns_client()

# --- DynamoDB Tables ---
def create_table(table_name, partition_key):
    """Create a DynamoDB table if it doesn't exist."""
    try:
        table = ddb.Table(table_name)
        table.load()
        print(f"Table '{table_name}' already exists.")
    except Exception:
        table = ddb.create_table(
            TableName=table_name,
            AttributeDefinitions=[{"AttributeName": partition_key, "AttributeType": "S"}],
            KeySchema=[{"AttributeName": partition_key, "KeyType": "HASH"}],
            BillingMode="PAY_PER_REQUEST"
        )
        table.wait_until_exists()
        print(f"Created table '{table_name}' successfully.")

# --- SQS Queue ---
def create_queue(queue_name):
    """Create an SQS queue if it doesn't exist."""
    resp = sqs.create_queue(QueueName=queue_name)
    print(f"Created queue '{queue_name}': {resp['QueueUrl']}")
    return resp['QueueUrl']

# --- SNS Topic ---
def create_topic(topic_name):
    """Create an SNS topic if it doesn't exist."""
    resp = sns.create_topic(Name=topic_name)
    print(f"Created SNS topic '{topic_name}': {resp['TopicArn']}")
    return resp['TopicArn']

# --- Main setup ---
if __name__ == "__main__":
    # Create DynamoDB tables
    create_table(ORDERS_TABLE, "order_id")
    create_table(INVENTORY_TABLE, "item_id")
    create_table(RECIPES_TABLE, "recipe_id")
    
    # Create SQS queue
    QUEUE_URL = create_queue(QUEUE_NAME)
    
    # Create SNS topic
    TOPIC_ARN = create_topic(SNS_TOPIC_NAME)
    
    print("\nInfrastructure setup completed successfully.")
    print(f"Orders Queue URL: {QUEUE_URL}")
    print(f"SNS Topic ARN: {TOPIC_ARN}")
