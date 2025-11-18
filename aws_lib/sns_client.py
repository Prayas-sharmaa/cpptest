from .base_client import AWSBaseClient

class SNSClient(AWSBaseClient):
    def __init__(self):
        super().__init__("sns")

    def publish(self, topic_arn, message):
        return self.client.publish(
            TopicArn=topic_arn,
            Message=message
        )
