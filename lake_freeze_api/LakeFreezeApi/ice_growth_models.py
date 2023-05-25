from data_models import WeatherByDay
from dataclasses import dataclass

def ashton_ice_growth(
            weather_days: list[WeatherByDay]            
        ):
    """http://lakeice.squarespace.com/ice-growth/"""

    # Units: meter per degree c per day
    GROWTH_RATE = - (
            1 / 15  # 1 inch per degree F per day
            * 0.0254 / 1  # 0.0254 meters per inch
            * 9 / 5 # degrees f per degree C
        )

    def get_fdd(weather_day: WeatherByDay):
            return weather_day.avg_temp_c * GROWTH_RATE

    # the average number of degrees below freezing over 24 hours
    initial_ice_thickness = 0
    
    return initial_ice_thickness + sum([get_fdd(weather_day) for weather_day in weather_days])