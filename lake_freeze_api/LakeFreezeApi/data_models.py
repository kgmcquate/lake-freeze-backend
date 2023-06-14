from sqlmodel import SQLModel, Field
from typing import Optional
import datetime

from sqlmodel import Session, select


class Lake(SQLModel, table=True):
    __tablename__ = "lakes"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    lake_name: str
    latitude: str = None
    longitude: str = None
    nearby_city_name: str = None
    state_or_province: str = None
    country: str = None
    nearby_city_latitude: str = None
    nearby_city_longitude: str = None
    max_depth_m: float = None
    surface_area_m2: float = None



class DailyWeather(SQLModel, table=True):
    __tablename__ = "daily_weather"

    date: datetime.date = Field(primary_key=True)
    latitude: str = Field(primary_key=True)
    longitude: str = Field(primary_key=True)
    timezone: str
    temperature_2m_max: float = Field(default=None)
    temperature_2m_min: float = Field(default=None)
    sunrise: datetime.date = Field(default=None)
    sunset: datetime.date = Field(default=None)
    uv_index_max: float = Field(default=None)
    uv_index_clear_sky_max: float = Field(default=None)
    precipitation_sum: float = Field(default=None)
    rain_sum: float = Field(default=None)
    showers_sum: float = Field(default=None)
    snowfall_sum: float = Field(default=None)
    precipitation_hours: float = Field(default=None)
    precipitation_probability_max: int = Field(default=None)
    windspeed_10m_max: float = Field(default=None)
    windgusts_10m_max: float = Field(default=None)
    winddirection_10m_dominant: int = Field(default=None)
    shortwave_radiation_sum: float = Field(default=None)
    et0_fao_evapotranspiration: float = Field(default=None)


# class WeatherByDay(SQLModel, table=True):
#     __tablename__ = "weather_by_day"
    
#     date: datetime.date = Field(primary_key=True)
#     latitude: float = Field(primary_key=True)
#     longitude: float = Field(primary_key=True)
#     nearby_city_name: str
#     state_or_province: str 
#     country: str
#     max_temp_c: float
#     min_temp_c: float
#     avg_temp_c: float
#     max_wind_kph: float
#     total_precip_mm: float
#     avg_visibility_km: float
#     avg_humidity: float
#     uv: float
#     last_updated_ts: Optional[datetime.datetime] = Field(default=datetime.datetime.now(datetime.timezone.utc))
    
    
class LakeWeatherReport(SQLModel, table=True):
    __tablename__ = "lake_freeze_reports"
    lake_id: int = Field(primary_key=True)
    date: datetime.date = Field(primary_key=True)
    ice_alg_version: str
    ice_m: float
    is_frozen: bool
    latitude: str
    longitude: str
    lake_name: str
    last_updated_ts: Optional[datetime.datetime] = Field(default=datetime.datetime.now(datetime.timezone.utc))
    
    