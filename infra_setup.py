# infra_setup.py
import os
from aws_config import dynamodb_resource, sqs_client, sns_client
import boto3

# Get environment variables
ORDERS_TABLE = os.getenv("DDB_ORDERS_TABLE", "Orders")
INVENTORY_TABLE = os.getenv("DDB_INVENTORY_TABLE", "Inventory")
RECIPES_TABLE = os.getenv("DDB_RECIPES_TABLE", "Recipes")
QUEUE_NAME = os.getenv("SQS_ORDER_QUEUE_NAME", "cloudkitchen-orders")
SNS_TOPIC_NAME = os.getenv("SNS_ORDER_TOPIC_NAME", "cloudkitchen-order-notifications")
S3_BUCKET_NAME = os.getenv("S3_RECIPE_BUCKET", "cloudkitchen-recipes")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")

# Initialize AWS clients/resources
ddb = dynamodb_resource()
sqs = sqs_client()
sns = sns_client()
s3 = boto3.client("s3", region_name=AWS_REGION)

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
    resp = sqs.create_queue(QueueName=queue_name)
    print(f"Created queue '{queue_name}': {resp['QueueUrl']}")
    return resp['QueueUrl']

# --- SNS Topic ---
def create_topic(topic_name):
    resp = sns.create_topic(Name=topic_name)
    print(f"Created SNS topic '{topic_name}': {resp['TopicArn']}")
    return resp['TopicArn']

# --- S3 Bucket ---
def create_bucket(bucket_name, region=AWS_REGION):
    existing_buckets = [b['Name'] for b in s3.list_buckets().get('Buckets', [])]
    if bucket_name in existing_buckets:
        print(f"S3 bucket '{bucket_name}' already exists.")
        return bucket_name

    if region == "us-east-1":
        s3.create_bucket(Bucket=bucket_name)
    else:
        s3.create_bucket(
            Bucket=bucket_name,
            CreateBucketConfiguration={'LocationConstraint': region}
        )
    print(f"Created S3 bucket '{bucket_name}' in region '{region}'.")
    return bucket_name

# --- Main setup ---
if __name__ == "__main__":
    create_table(ORDERS_TABLE, "order_id")
    create_table(INVENTORY_TABLE, "item_id")
    create_table(RECIPES_TABLE, "recipe_id")

    QUEUE_URL = create_queue(QUEUE_NAME)
    TOPIC_ARN = create_topic(SNS_TOPIC_NAME)
    BUCKET_NAME = create_bucket(S3_BUCKET_NAME)

    print("\nInfrastructure setup completed successfully.")
    print(f"Orders Queue URL: {QUEUE_URL}")
    print(f"SNS Topic ARN: {TOPIC_ARN}")
    print(f"S3 Bucket Name: {BUCKET_NAME}")
