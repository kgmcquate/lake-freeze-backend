import os, json, boto3
import pandas as pd
import sqlalchemy

secret_arn = os.environ.get("DB_CREDS_SECRET_ARN", "arn:aws:secretsmanager:us-east-1:117819748843:secret:rds-lake-freeze-credentials-5gwihC")

db_endpoint = os.environ.get("DB_ENDPOINT" , "lake-freeze-backend-db.cluster-cu0bcthnum69.us-east-1.rds.amazonaws.com")


# print("getting creds from sm")
secret = json.loads(
        boto3.client("secretsmanager", 'us-east-1')
        .get_secret_value(SecretId=secret_arn)
        ["SecretString"]
)

db_username = secret["username"]

db_password = secret["password"]

engine = sqlalchemy.create_engine(f'postgresql+psycopg2://{db_username}:{db_password}@{db_endpoint}') #/lake_freeze





from pynamodb.models import Model
from pynamodb.attributes import NumberAttribute, UnicodeAttribute
from pynamodb.indexes import GlobalSecondaryIndex, AllProjection, KeysOnlyProjection

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


import datetime
from pynamodb.attributes import Attribute, ListAttribute, MapAttribute
from pynamodb.constants import NUMBER, STRING

class DateAttribute(Attribute[datetime.date]):
    """Represents a date as an integer (e.g. 2015_12_31 for December 31st, 2015)."""

    attr_type = NUMBER

    def serialize(self, value: datetime.date) -> str:
        return json.dumps(value.year * 1_00_00 + value.month * 1_00 + value.day)

    def deserialize(self, value: str) -> datetime.date:
        n = json.loads(value)
        return datetime.date(n // 1_00_00, n // 1_00 % 1_00, n % 1_00)



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

Lake.create_table(wait=True, billing_mode='PAY_PER_REQUEST')

# WeatherByDay.create_table(wait=True, billing_mode='PAY_PER_REQUEST')

import numpy as np


# lakes_df = pd.read_sql('select * from lakes',con=engine)
# lakes_df = lakes_df.replace({np.nan: None})


# with Lake.batch_write() as batch:
#     for i, row in lakes_df.iterrows():
        

#         lat_long = str(row.latitude) + ',' + str(row.longitude)
        
#         d = dict(row)

#         lake = Lake(**d, lat_long=lat_long )
#         batch.save(lake)


# weather_df = pd.read_sql('select * from weather_by_day',con=engine)
# weather_df = weather_df.replace({np.nan: None})

# # weather_df['date_'] = weather_df['date']
# del weather_df['last_updated_ts']


# with WeatherByDay.batch_write() as batch:
#     for i, row in weather_df.iterrows():
        
#         lat_long = str(row.latitude) + ',' + str(row.longitude)
        
#         d = dict(row)

#         w = WeatherByDay(**d, lat_long=lat_long )
#         batch.save(w)
