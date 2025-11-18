import boto3

def get_sns_topic_arn(topic_name: str, region: str = "us-east-1") -> str:
    """
    Fetch SNS Topic ARN dynamically by topic name.
    Raises ValueError if topic is not found.
    """
    sns_client = boto3.client("sns", region_name=region)
    
    next_token = None
    while True:
        if next_token:
            response = sns_client.list_topics(NextToken=next_token)
        else:
            response = sns_client.list_topics()
        
        for topic in response.get("Topics", []):
            arn = topic["TopicArn"]
            if topic_name in arn:
                return arn
        
        next_token = response.get("NextToken")
        if not next_token:
            break

    raise ValueError(f"SNS Topic '{topic_name}' not found in region {region}")
