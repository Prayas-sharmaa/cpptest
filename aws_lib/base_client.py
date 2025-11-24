import boto3

class AWSBaseClient:
    """
    Base AWS client that creates a NEW boto3 session every time
    to avoid expired Cloud9 temporary credentials.
    """

    def __init__(self, service_name, region_name="us-east-1"):
        self.service_name = service_name
        self.region_name = region_name

    @property
    def client(self):
        # ALWAYS returns a fresh client with fresh credentials
        session = boto3.Session()
        return session.client(self.service_name, region_name=self.region_name)

    @property
    def resource(self):
        # ALWAYS returns a fresh resource with fresh credentials
        session = boto3.Session()
        return session.resource(self.service_name, region_name=self.region_name)
