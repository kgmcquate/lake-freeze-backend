import datetime

from data_models import Lake, WeatherByDay


def get_weather_data(latitude: float, longitude: float, date: datetime.date) -> WeatherByDay:
    def coalesce(val1, val2):
        if val1 is not None:
                return val1
        else:
                return val2 

            
    query = f"{latitude},{longitude}"
            

    resp = requests.get(
            base_url, 
            params={"key": api_key, 
                    "q": query, 
                    "dt": str(date)
                    }
        ).json()
    
    
    # make sure its pulling from the correct location
    assert abs(latitude - resp['location']['lat']) < 0.001
    
    assert abs(longitude - resp['location']['lon']) < 0.001
    
    weather_by_day = WeatherByDay(
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