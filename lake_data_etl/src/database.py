import sqlmodel
import json
import os
import boto3
from sqlmodel import create_engine

secret_arn = os.environ.get("DB_CREDS_SECRET_ARN", "arn:aws:secretsmanager:us-east-1:117819748843:secret:rds-lake-freeze-credentials-5gwihC")

db_endpoint = os.environ.get("DB_ENDPOINT" , "lake-freeze-backend-db.cluster-cu0bcthnum69.us-east-1.rds.amazonaws.com")


# print("getting creds from sm")
secret = json.loads(
        boto3.client("secretsmanager", 'us-east-1')
        .get_secret_value(SecretId=secret_arn)
        ["SecretString"]
)

# db_username = secret["username"]

# db_password = secret["password"]

db_username = "postgres" #secret["username"]

db_password = "m9Zo5DbX" #secret["password"]


# aws_access_key_id = 'ASIARW3U2WHVQJ2AJY4X'
# aws_secret_access_key = 'YDmnMgvgVhYgP2w4HlcsoUF4/Z2caEpcHRmZZCAo'

# engine = create_engine(f"amazondynamodb:///?Access Key={aws_access_key_id}&Secret Key={aws_secret_access_key}&Domain=amazonaws.com&Region=us-east-1")


# print("creating engine")
engine = sqlmodel.create_engine(f'postgresql+psycopg2://{db_username}:{db_password}@{db_endpoint}') #/lake_freeze



