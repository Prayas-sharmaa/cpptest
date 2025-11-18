from .base_client import AWSBaseClient
from decimal import Decimal

class DynamoDBClient(AWSBaseClient):
    def __init__(self):
        super().__init__("dynamodb")

    # --------------------------
    # Helpers
    # --------------------------

    def _deserialize(self, value):
        """Convert DynamoDB data into plain Python types."""
        if isinstance(value, dict):
            # DynamoDB structured value like {"N": "5"} handled automatically by boto3?
            # But your previous implementation overrides it, so we fix it.
            # We assume normal boto3 resource returns plain dict, not attribute dict.
            return {k: self._deserialize(v) for k, v in value.items()}
        if isinstance(value, list):
            return [self._deserialize(v) for v in value]
        if isinstance(value, Decimal):
            return int(value) if value % 1 == 0 else float(value)
        return value

    # --------------------------
    # Public CRUD
    # --------------------------

    def put(self, table, item):
        tbl = self.resource.Table(table)
        # Convert Python ints to Decimal to avoid Dynamo issues
        clean_item = self._convert_to_decimal(item)
        return tbl.put_item(Item=clean_item)

    def get(self, table, key):
        tbl = self.resource.Table(table)
        resp = tbl.get_item(Key=key)
        item = resp.get("Item")
        return self._deserialize(item) if item else {}

    def scan(self, table):
        tbl = self.resource.Table(table)
        resp = tbl.scan()
        items = resp.get("Items", [])
        return [self._deserialize(i) for i in items]

    # --------------------------
    # Convert all ints → Decimal
    # --------------------------
    def _convert_to_decimal(self, data):
        """Recursively convert ints to Decimal for DynamoDB put_item."""
        if isinstance(data, dict):
            return {k: self._convert_to_decimal(v) for k, v in data.items()}
        if isinstance(data, list):
            return [self._convert_to_decimal(v) for v in data]
        if isinstance(data, int):
            return Decimal(data)
        return data
