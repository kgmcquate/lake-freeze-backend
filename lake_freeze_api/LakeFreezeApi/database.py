import sqlmodel
import json
import os
import boto3

secret_arn = os.environ.get("DB_CREDS_SECRET_ARN", "arn:aws:secretsmanager:us-east-1:117819748843:secret:rds-lake-freeze-credentials-5gwihC")

db_endpoint = os.environ.get("DB_ENDPOINT" , "lake-freeze-backend-db.cluster-cu0bcthnum69.us-east-1.rds.amazonaws.com")

secret = json.loads(
        boto3.client("secretsmanager", 'us-east-1')
        .get_secret_value(SecretId=secret_arn)
        ["SecretString"]
)

db_username = secret["username"]

db_password = secret["password"]

engine = sqlmodel.create_engine(f'postgresql+psycopg2://{db_username}:{db_password}@{db_endpoint}') #/lake_freeze


