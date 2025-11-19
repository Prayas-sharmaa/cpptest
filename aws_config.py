# aws_config.py
import boto3
from botocore.config import Config

# -----------------------------
# AWS region & boto3 config
# -----------------------------
AWS_REGION = "us-east-1"  # Cloud9 defaults to its instance region if not set

boto3_config = Config(
    region_name=AWS_REGION,
    retries={"max_attempts": 3, "mode": "standard"}
)

# -----------------------------
# AWS clients/resources
# -----------------------------
def dynamodb_resource():
    return boto3.resource("dynamodb", region_name=AWS_REGION, config=boto3_config)

def dynamodb_client():
    return boto3.client("dynamodb", region_name=AWS_REGION, config=boto3_config)

def sqs_client():
    return boto3.client("sqs", region_name=AWS_REGION, config=boto3_config)

def sns_client():
    return boto3.client("sns", region_name=AWS_REGION, config=boto3_config)

# -----------------------------
# SQS & SNS configuration
# -----------------------------
DEFAULT_QUEUE_NAME = "cloudkitchen-orders-queue"
DEFAULT_SNS_TOPIC_NAME = "cloudkitchen-order-notifications"

def get_sqs_url():
    sqs = sqs_client()
    try:
        resp = sqs.get_queue_url(QueueName=DEFAULT_QUEUE_NAME)
        return resp["QueueUrl"]
    except sqs.exceptions.QueueDoesNotExist:
        # Queue does not exist → create it
        resp = sqs.create_queue(
            QueueName=DEFAULT_QUEUE_NAME,
            Attributes={
                "DelaySeconds": "0",
                "MessageRetentionPeriod": "86400"  # 1 day
            }
        )
        return resp["QueueUrl"]

def get_sns_topic_arn():
    sns = sns_client()
    # Check if topic exists
    topics = sns.list_topics()["Topics"]
    for t in topics:
        if t["TopicArn"].endswith(DEFAULT_SNS_TOPIC_NAME):
            return t["TopicArn"]
    # Topic does not exist → create it
    resp = sns.create_topic(Name=DEFAULT_SNS_TOPIC_NAME)
    return resp["TopicArn"]
