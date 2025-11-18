import boto3

class AWSBaseClient:
    def __init__(self, service_name):
        self.client = boto3.client(service_name, region_name="us-east-1")
        self.resource = (
            boto3.resource(service_name, region_name="us-east-1")
            if service_name not in ["sns", "sqs"]
            else None
        )
