from .base_client import AWSBaseClient

class SQSClient(AWSBaseClient):
    def __init__(self):
        super().__init__("sqs")

    def send_message(self, queue_url, body):
        return self.client.send_message(
            QueueUrl=queue_url,
            MessageBody=body
        )

    def receive_messages(self, queue_url, max_messages=1):
        resp = self.client.receive_message(
            QueueUrl=queue_url,
            MaxNumberOfMessages=max_messages,
            WaitTimeSeconds=5
        )
        return resp.get("Messages", [])
