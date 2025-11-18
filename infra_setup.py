import boto3

def create_tables():
    dynamodb = boto3.client("dynamodb")

    # Orders Table
    dynamodb.create_table(
        TableName='Orders',
        KeySchema=[{'AttributeName': 'order_id', 'KeyType': 'HASH'}],
        AttributeDefinitions=[{'AttributeName': 'order_id', 'AttributeType': 'S'}],
        BillingMode='PAY_PER_REQUEST'
    )

    # Inventory Table
    dynamodb.create_table(
        TableName='Inventory',
        KeySchema=[{'AttributeName': 'item_id', 'KeyType': 'HASH'}],
        AttributeDefinitions=[{'AttributeName': 'item_id', 'AttributeType': 'S'}],
        BillingMode='PAY_PER_REQUEST'
    )

def create_queue():
    sqs = boto3.client("sqs")
    sqs.create_queue(QueueName="OrderQueue")

def create_sns():
    sns = boto3.client("sns")
    sns.create_topic(Name="LowStockAlerts")

if __name__ == "__main__":
    create_tables()
    create_queue()
    create_sns()
    print("AWS Infrastructure Created Successfully!")
