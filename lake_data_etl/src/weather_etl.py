import json
import requests
import boto3
import sqlmodel
from sqlmodel import SQLModel, Field
from typing import Optional
# from datetime import date, datetime
import datetime


secret_arn = "arn:aws:secretsmanager:us-east-1:117819748843:secret:weather-api-credentials-Fp6sTu"


base_url = "http://api.weatherapi.com/v1/history.json"


secret = json.loads(
        boto3.client("secretsmanager", 'us-east-1')
        .get_secret_value(SecretId=secret_arn)
        ["SecretString"]
)

api_key = secret["key"]


class Lake(SQLModel, table=True):
        __tablename__ = "lakes"

        id: Optional[int] = Field(default=None, primary_key=True)
        lake_name: str
        nearby_city_name: str = None
        state_or_province: str = None
        country: str = None
        latitude: float = None
        longitude: float = None
        max_depth_m: float
        surface_area_m2: float


class WeatherByDay(SQLModel, table=True):
        __tablename__ = "weather_by_day"
    
        date: datetime.date
        nearby_city_name: str
        state_or_province: str 
        country: str
        latitude: float
        longitude: float
        max_temp_c: float
        min_temp_c: float
        avg_temp_c: float
        max_wind_kph: float
        total_precip_mm: float
        avg_visibility_km: float
        avg_humidity: float
        uv: float


def get_hourly_data(lake: Lake, date: datetime.date):
        def coalesce(val1, val2):
                if val1 is not None:
                        return val1
                else:
                        return val2 


        if lake.nearby_city_name is not None and lake.state_or_province is not None:
                query = f"{lake.nearby_city_name},{lake.state_or_province}"
        else:
                query = f"{lake.latitiude},{lake.longitude}"

        resp = requests.get(base_url, 
                            params={"key": api_key, 
                                    "q": query, 
                                    "dt": str(date)
                                    }
                            )
        return WeatherByDay(
                date=date,
                nearby_city_name=coalesce(
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
