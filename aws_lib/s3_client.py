from .base_client import AWSBaseClient

class S3Client(AWSBaseClient):
    def __init__(self):
        super().__init__("s3")

    def upload_file(self, bucket, key, file_path):
        self.client.upload_file(file_path, bucket, key)
        return f"s3://{bucket}/{key}"
