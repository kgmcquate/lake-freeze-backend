import json
# import requests
import boto3

secret_arn = "arn:aws:secretsmanager:us-east-1:117819748843:secret:weather-api-credentials-Fp6sTu"


base_url = "http://api.weatherapi.com/v1/history.json"


secret = json.loads(
        boto3.client("secretsmanager", 'us-east-1')
        .get_secret_value(SecretId=secret_arn)
        ["SecretString"]
)

api_key = secret["key"]
print(api_key)
