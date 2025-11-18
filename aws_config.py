import boto3

def get_sqs_url(queue_name="OrderQueue", region="us-east-1"):
    sqs_client = boto3.client("sqs", region_name=region)
    return sqs_client.get_queue_url(QueueName=queue_name)['QueueUrl']

def get_sns_topic_arn(topic_name="LowStockAlerts", region="us-east-1"):
    sns_client = boto3.client("sns", region_name=region)
    response = sns_client.list_topics()
    for topic in response['Topics']:
        if topic_name in topic['TopicArn']:
            return topic['TopicArn']
    raise ValueError(f"Topic {topic_name} not found")
