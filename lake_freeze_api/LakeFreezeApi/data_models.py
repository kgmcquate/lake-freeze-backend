from sqlmodel import SQLModel, Field
from typing import Optional
import datetime

from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import JSONB

class WaterBody(SQLModel, table=True):
    __tablename__ = "water_bodies"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    longitude: str = None
    latitude: str = None
    name: str = None
    max_depth_m: float = None
    areasqkm: float = None
    elevation: Optional[float] = Field(default=None)
    min_latitude: float = None
    max_latitude: float = None
    min_longitude: float = None
    max_longitude: float = None

class WaterBodyGeometry(SQLModel, table=True):
    __tablename__ = "water_body_geometries"
    class Config:
        arbitrary_types_allowed = True
        response_model=None

    id: Optional[int] = Field(default=None, primary_key=True)
    boundary: JSONB = Field(default=None, sa_column=Column(JSONB))
    bounding_box: JSONB = Field(default=None, sa_column=Column(JSONB))
    geometry: JSONB = Field(default=None, sa_column=Column(JSONB))


class DailyWeather(SQLModel, table=True):
    __tablename__ = "daily_weather"

    date: datetime.date = Field(primary_key=True)
    latitude: str = Field(primary_key=True)
    longitude: str = Field(primary_key=True)
    timezone: str
    temperature_2m_max: float = Field(default=None)
    temperature_2m_min: float = Field(default=None)
    sunrise: datetime.datetime = Field(default=None)
    sunset: datetime.datetime = Field(default=None)
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

  
class WaterBodyWeatherReport(SQLModel, table=True):
    __tablename__ = "waterbody_weather_reports"
    waterbody_id: int = Field(primary_key=True)
    date: datetime.date = Field(primary_key=True)
    ice_alg_version: str
    ice_m: float
    is_frozen: bool
    latitude: str
    longitude: str
    waterbody_name: str
    last_updated_ts: Optional[datetime.datetime] = Field(default=datetime.datetime.now(datetime.timezone.utc))
    

class WaterBodySatelliteImage(SQLModel, table=True):    
    __tablename__ = "waterbody_satellite_images"

    waterbody_id: int = Field(primary_key=True)
    captured_ts: datetime.datetime = Field(primary_key=True)
    satellite_dataset: str
    ee_id: str 
    properties: str = Field(default=None, sa_column=Column(JSONB))
    filename: str
    thumbnail_filename: str
    red_average: float
    green_average: float
    blue_average: float
