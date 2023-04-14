from dataclasses import dataclass
from bs4 import BeautifulSoup
import requests
import pandas as pd

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
            

    # print(tables)

