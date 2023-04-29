
import json
import datetime

from pynamodb.models import Model
from pynamodb.attributes import Attribute, ListAttribute, MapAttribute, NumberAttribute, UnicodeAttribute, BooleanAttribute
from pynamodb.constants import NUMBER, STRING
from pynamodb.indexes import GlobalSecondaryIndex, AllProjection, KeysOnlyProjection

class DateAttribute(Attribute[datetime.date]):
    """Represents a date as an integer (e.g. 2015_12_31 for December 31st, 2015)."""

    attr_type = NUMBER

    def serialize(self, value: datetime.date) -> str:
        return json.dumps(value.year * 1_00_00 + value.month * 1_00 + value.day)

    def deserialize(self, value: str) -> datetime.date:
        n = json.loads(value)
        return datetime.date(n // 1_00_00, n // 1_00 % 1_00, n % 1_00)


class LatitudeIndex(GlobalSecondaryIndex):
    class Meta:
        read_capacity_units = 1
        write_capacity_units = 1
        projection = AllProjection()

    latitude = NumberAttribute(hash_key=True)

class LongitudeIndex(GlobalSecondaryIndex):
    class Meta:
        read_capacity_units = 1
        write_capacity_units = 1
        projection = AllProjection()

    longitude = NumberAttribute(hash_key=True)


APP_NAME = "lake_freeze"
class Lake(Model):
    class Meta:
        table_name = f"{APP_NAME}.lakes"
        read_capacity_units = 1
        write_capacity_units = 1
    
    id = NumberAttribute(hash_key=True)
    lake_name = UnicodeAttribute(null=False)
    lat_long = UnicodeAttribute(null=True)
    latitude = NumberAttribute(null=True)
    longitude = NumberAttribute(null=True)
    nearby_city_name = UnicodeAttribute(null=True)
    state_or_province = UnicodeAttribute(null=True)
    country = UnicodeAttribute(null=True)
    nearby_city_latitude = NumberAttribute(null=True)
    nearby_city_longitude = NumberAttribute(null=True)
    max_depth_m = NumberAttribute(null=True)
    surface_area_m2 = NumberAttribute(null=True)

    latitude_index = LatitudeIndex()
    longitude_index = LongitudeIndex()


class WeatherByDay(Model):
    class Meta:
        table_name = f"{APP_NAME}.weather_by_day"
        read_capacity_units = 1
        write_capacity_units = 1
    
    lat_long = UnicodeAttribute(hash_key=True)
    date = DateAttribute(range_key=True)
    latitude = NumberAttribute(null=True)
    longitude = NumberAttribute(null=True)
    nearby_city_name = UnicodeAttribute(null=True)
    state_or_province = UnicodeAttribute(null=True)
    country = UnicodeAttribute(null=True)
    max_temp_c = NumberAttribute(null=True)
    min_temp_c = NumberAttribute(null=True)
    avg_temp_c = NumberAttribute(null=True)
    max_wind_kph = NumberAttribute(null=True)
    total_precip_mm = NumberAttribute(null=True)
    avg_visibility_km = NumberAttribute(null=True)
    avg_humidity = NumberAttribute(null=True)
    uv = NumberAttribute(null=True)
    
    
class LakeFreezeReport(Model):
    class Meta:
        table_name = f"{APP_NAME}_lake_freeze_reports"
        read_capacity_units = 1
        write_capacity_units = 1
    
    lake_id = NumberAttribute(hash_key=True)
    date = DateAttribute(range_key=True)
    ice_m = NumberAttribute(null=True)
    is_frozen = BooleanAttribute(null=True)
    
    