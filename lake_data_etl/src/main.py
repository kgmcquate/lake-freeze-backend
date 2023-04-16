from dataclasses import dataclass
from bs4 import BeautifulSoup
import requests
import pandas as pd
import boto3
import json
import sqlalchemy
from sqlalchemy.sql import text


secret = json.loads(
        boto3.client("secretsmanager", 'us-east-1')
        .get_secret_value(SecretId="arn:aws:secretsmanager:us-east-1:117819748843:secret:rds-lake-freeze-credentials-5gwihC")
        ["SecretString"]
)

db_username = secret["username"]

db_password = secret["password"]

db_endpoint = "lake-freeze-backend-db.cluster-cu0bcthnum69.us-east-1.rds.amazonaws.com"


 
engine = sqlalchemy.create_engine(f'postgresql+psycopg2://{db_username}:{db_password}@{db_endpoint}') #/lake_freeze


# with engine.connect() as conn:
#     for row in conn.execute(text("SELECT 6")):
#         print(row)
    

states = ["Minnesota"]

def clean_colname(colname):
    return colname.lower().strip().replace(" ", "_").replace("\n", "")

# https://www.dnr.state.mn.us/lakefind/lake.html?id=27003100

for state in states:
    url = f"https://en.wikipedia.org/wiki/List_of_lakes_of_{state}"

    resp = requests.get(url)
    
    soup = BeautifulSoup(resp.text, 'html.parser')

    tables = soup.find_all('table', class_="wikitable sortable")

    if len(tables) != 1:
        raise Exception(f"Bad tables {state}")

    table = tables[0]

    colnames = [clean_colname(c.text) for c in table.find_all('th')]
    print(colnames)


    rows = []
    for row in table.tbody.find_all('tr'):
        cols = row.find_all('td')

        clean_row = []
        for c in cols:
            link = c.find('a')  # Sometimes theres a link for the name with extra text
            if link:
                clean_row.append(link.text.strip())
            else:
                clean_row.append(c.text.strip())

        rows.append(clean_row)

    df = pd.DataFrame(rows, columns=colnames )
    print(df.head())

    df.to_sql(name='lakes', con=engine, if_exists='replace')

