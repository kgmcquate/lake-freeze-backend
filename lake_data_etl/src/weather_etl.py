import json
import requests
import boto3
import sqlmodel
from sqlmodel import SQLModel, Field
from typing import Optional
# from datetime import date, datetime
import datetime

from sqlmodel import Session, select

from data_models import Lake, WeatherByDay

from database import engine



base_url = "http://api.weatherapi.com/v1/history.json"


secret = json.loads(
        boto3.client("secretsmanager", 'us-east-1')
        .get_secret_value(SecretId=secret_arn)
        ["SecretString"]
)

api_key = "f05c945b0eb94da580d222013232104" # secret["key"]

db_username = "postgres" #secret["username"]

db_password = "m9Zo5DbX" #secret["password"]

# WeatherByDay.__table__.drop(engine)


def get_weather_data(lake: Lake, date: datetime.date):
        def coalesce(val1, val2):
                if val1 is not None:
                        return val1
                else:
                        return val2 

        # if lake.latitiude is not None and lake.longitude is not None:
        #         query = f"{lake.latitiude},{lake.longitude}"
                
        # elif lake.nearby_city_name is not None and lake.state_or_province is not None:
        #         query = f"{lake.nearby_city_name},{lake.state_or_province}"
        # else:
                
        query = f"{lake.nearby_city_name},{lake.state_or_province}"
                

        resp = requests.get(base_url, 
                            params={"key": api_key, 
                                    "q": query, 
                                    "dt": str(date)
                                    }
                            ).json()
                            
        weather_by_day = WeatherByDay(
                date=date,
                city_name=coalesce(
                        lake.nearby_city_name, 
                        resp['location']['name'].lower()
                ),
                state_or_province=coalesce(
                        lake.state_or_province,
                        resp['location']['region'].lower()
                ),
                country=coalesce(
                        lake.country,
                        resp['location']['country'].lower()
                ),
                latitude=coalesce(lake.latitude, resp['location']['lat']),
                longitude=coalesce(lake.longitude, resp['location']['lon']),
                max_temp_c=resp['forecast']['forecastday'][0]['day']['maxtemp_c'],
                min_temp_c=resp['forecast']['forecastday'][0]['day']['mintemp_c'],
                avg_temp_c=resp['forecast']['forecastday'][0]['day']['avgtemp_c'],
                max_wind_kph=resp['forecast']['forecastday'][0]['day']['maxwind_kph'],
                total_precip_mm=resp['forecast']['forecastday'][0]['day']['totalprecip_mm'],
                avg_visibility_km=resp['forecast']['forecastday'][0]['day']['avgvis_km'],
                avg_humidity=resp['forecast']['forecastday'][0]['day']['avghumidity'],
                uv=resp['forecast']['forecastday'][0]['day']['uv']
        )


        return  weather_by_day
        

# SQLModel.metadata.create_all(engine)

lakes = []

with Session(engine) as session:
        statement = select(Lake)
        
        print("executing statement")
        lakes = session.exec(statement).all()


weather_by_days = []
for lake in lakes:
        weather_by_days.append(
                get_weather_data(lake, datetime.datetime.today().date())
        )

print(weather_by_days)

with Session(engine) as session:
        for w in weather_by_days:
                session.add(w)
        
        session.flush()