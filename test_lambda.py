import boto3
import json
from lambda_order_processor import lambda_handler  # your lambda

def load_test_event():
    return {
        "Records": [
            {
                "body": json.dumps({
                    "order_id": "4511fefe-a84d-4d99-b4e4-945f8dd11621",
                    "recipe": "ab1e18ea-6a06-412b-ac37-1e06960b6e44"
                })
            }
        ]
    }

if __name__ == "__main__":
    event = load_test_event()
    print(lambda_handler(event, None))
