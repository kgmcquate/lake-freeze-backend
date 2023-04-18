from dataclasses import dataclass
from bs4 import BeautifulSoup
import requests
import pandas as pd
import boto3
import json
import sqlalchemy
from sqlalchemy.sql import text



from sqlalchemy import  MetaData, Table, Column, Integer, String, Float


metadata = MetaData()

lakes_table = Table('lakes', metadata,
    Column('lake', String),
    Column('nearby_town', String),
    Column('surface_area_m2', Float),
    Column('max_depth_m', Float)
)



metadata.create_all(engine)


# ['lake', 'nearby_town', 'size(acres)',  'max_depth(ft)']

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
    
    
    df.dropna(inplace=True)
    
    def convert_to_float(s):
        s = s.replace(",", "").strip()
        try:
            return float(s)
        except ValueError as e:
            return None
            
    df['size(acres)'] = df['size(acres)'].apply(convert_to_float)
    
    df['max_depth(ft)'] = df['max_depth(ft)'].apply(convert_to_float)
    
    # df = df[~df["size(acres)"].str.contains(";")]
    # df = df[df["size(acres)"].str.len() > 0]
    
    # df['size(acres)'] = df['size(acres)'].str.replace(",", "").astype(float, errors='ignore')
    # df = df[df['size(acres)'].dtype == float]
    
    df['surface_area_m2'] = df['size(acres)'] * 4046.8564224
    
    df['max_depth_m'] = df['max_depth(ft)'] * 0.3048
    
    df['name'] = df['lake']
    
    df = df[['name', 'nearby_town', 'surface_area_m2',  'max_depth_m']]
    
    print(df.head())

    df.to_sql(name='lakes', con=engine, if_exists='replace')

