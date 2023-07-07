import datetime
import requests
from data_models import DailyWeather
import boto3
import json
import os

weather_base_url = "http://api.weatherapi.com/v1/history.json"

weather_api_key_secret_arn = os.environ.get("WEATHER_API_KEY_SECRET" , "arn:aws:secretsmanager:us-east-1:117819748843:secret:weather-api-credentials-Fp6sTu")

print("getting weather api secret")
weather_api_secret = json.loads(
        boto3.client("secretsmanager", 'us-east-1')
        .get_secret_value(SecretId=weather_api_key_secret_arn)
        ["SecretString"]
)

weather_api_key = weather_api_secret["key"]


def get_weather_data(latitude: float, longitude: float, date: datetime.date) -> DailyWeather:
            
    query = f"{latitude},{longitude}"
            
#     print(f"Getting weather for {date} {query}")
    resp = requests.get(
            weather_base_url, 
            params={"key": weather_api_key, 
                    "q": query, 
                    "dt": str(date)
                    }
        )
    
    resp.raise_for_status()

    resp = resp.json()
    
    
    # make sure its pulling from the correct location
#     print(f"{latitude=}")
#     try:
#         print(f"{resp['location']['lat']=}")
#     except Exception as e:
#           print(e)

    # assert abs(latitude - resp['location']['lat']) < 0.1
    
    # assert abs(longitude - resp['location']['lon']) < 0.1
    
    weather_by_day = DailyWeather(
            date=date,
            nearby_city_name=resp['location'].get('name').lower(),
            state_or_province=resp['location'].get('region').lower(),
            country= resp['location'].get('country').lower(),
            latitude=latitude,
            longitude=longitude,
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