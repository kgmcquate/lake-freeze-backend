from data_models import DailyWeather
from dataclasses import dataclass

import os 
import datetime



def ashton_ice_growth(
            weather_days: list[DailyWeather]            
        ):
    """http://lakeice.squarespace.com/ice-growth/"""

    # Units: meter per degree c per day
    GROWTH_RATE = - (
            1 / 15  # 1 inch per degree F per day
            * 0.0254 / 1  # 0.0254 meters per inch
            * 9 / 5 # degrees f per degree C
        )

    def get_fdd(weather_day: DailyWeather):
            return (weather_day.temperature_2m_min + weather_day.temperature_2m_max) / 2 * GROWTH_RATE

    # the average number of degrees below freezing over 24 hours
    initial_ice_thickness = 0

    ice_thickness = initial_ice_thickness + sum([get_fdd(weather_day) for weather_day in weather_days])
    
    if ice_thickness <= 0:
          return 0.0
    
    return ice_thickness

def white_fraction_xgb(
        date: datetime.date,
        latitude: float,
        longitude: float
    ) -> float:
    
    import xgboost as xgb

    model = xgb.Booster()

    model_file_path = os.path.join(
          os.path.dirname(os.path.abspath(__file__)),
          "model_objects",
          "white_fraction_model.json"
    )
    model.load_model(model_file_path)

    year = date.year
    month = date.month
    day_of_year = date.timetuple().tm_yday

    pred = model.predict(
        xgb.DMatrix(
            data=[[year, month, day_of_year, latitude, longitude]]
        ) 
        
    )

    return float(pred[0])