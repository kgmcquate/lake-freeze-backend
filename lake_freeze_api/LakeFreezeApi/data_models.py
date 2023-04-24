from sqlmodel import SQLModel, Field
from typing import Optional
import datetime

from sqlmodel import Session, select


class Lake(SQLModel, table=True):
    __tablename__ = "lakes"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    lake_name: str
    latitude: float = None
    longitude: float = None
    nearby_city_name: str = None
    state_or_province: str = None
    country: str = None
    nearby_city_latitude: float = None
    nearby_city_longitude: float = None
    max_depth_m: float = None
    surface_area_m2: float = None

    
class WeatherByDay(SQLModel, table=True):
    __tablename__ = "weather_by_day"
    
    date: datetime.date = Field(primary_key=True)
    latitude: float = Field(primary_key=True)
    longitude: float = Field(primary_key=True)
    nearby_city_name: str
    state_or_province: str 
    country: str
    max_temp_c: float
    min_temp_c: float
    avg_temp_c: float
    max_wind_kph: float
    total_precip_mm: float
    avg_visibility_km: float
    avg_humidity: float
    uv: float
    last_updated_ts: Optional[datetime.datetime] = Field(default=datetime.datetime.now(datetime.timezone.utc))
    
    
class LakeFreezeReport(SQLModel, table=True):
    __tablename__ = "lake_freeze_reports"
    
    lake_id: int = Field(primary_key=True)
    date: datetime.date = Field(primary_key=True)
    ice_alg_version: str
    ice_m: float
    is_frozen: bool
    last_updated_ts: Optional[datetime.datetime] = Field(default=datetime.datetime.now(datetime.timezone.utc))
    
    