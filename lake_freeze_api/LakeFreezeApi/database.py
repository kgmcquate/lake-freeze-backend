import sqlmodel
import json
import os
import boto3

secret_uri = os.environ.get("DB_CREDS_SECRET_S3_URI", "s3://secrets-zone-117819748843/lake_freeze_credentials.json")

db_endpoint = os.environ.get("DB_ENDPOINT" , "lake-freeze-db.cu0bcthnum69.us-east-1.rds.amazonaws.com")


print("getting db creds from s3")

secret_bucket, secret_key = secret_uri[5:].split("/", 2)
secret = json.loads(
        boto3.client("s3")
        .get_object(Bucket=secret_bucket, Key=secret_key)
        ["Body"]
        .read().decode("utf-8")
)

db_username = secret["username"]

db_password = secret["password"]


print("creating engine")
engine = sqlmodel.create_engine(f'postgresql+psycopg2://{db_username}:{db_password}@{db_endpoint}', echo=True) #/lake_freeze



