from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from mangum import Mangum
import json
import boto3
from typing import Optional
import datetime

from data_models import Lake, WeatherByDay, LakeFreezeReport
from external_api_calls import get_weather_data

app = FastAPI(debug=True)

import logging



@app.get("/home", response_class=HTMLResponse)
def get_home_page():
    return """
    <html>
        <body>
         Hello World
        </body>
    </html>
    """


@app.get("/lakes")
def get_lakes(
        min_surface_area: Optional[float] = None,
        max_surface_area: Optional[float] = None,
        min_latitude: float = -90.0,
        max_latitude: float = 90.0,
        min_longitude: float = -180.0,
        max_longitude: float = 180.0,
        limit: int = 100
    ):

    print("here")
    
    filters = []
        
    # if min_surface_area:
    #     filters.append(Lake.surface_area_m2 >= min_surface_area)
    # if max_surface_area:
    #     filters.append(Lake.surface_area_m2 < max_surface_area)

    latitude_index

    lakes = [lake.as_dict() for lake in Lake.query(hash_key= , *filters)]
    # print(lakes)
    return [1,2,3]
    
    

# @app.get("/lake_freeze_reports")
# def get_lake_freeze_reports(
#         lake_id: int, 
#         date: datetime.date = datetime.datetime.today().date()
#     )-> LakeFreezeReport:

#     logger = logging.getLogger()

#     logger.setLevel(logging.INFO)
            
#     WEATHER_LOOKBACK_DAYS = 30

#     min_date = date - datetime.timedelta(days=WEATHER_LOOKBACK_DAYS)
    
#     with Session(engine) as session:
#         lake: Lake = session.get(Lake, lake_id)

#     logger.setLevel(logging.INFO)
#     # logger.warn(f"{lake=}")
        
        
#     statement = select(WeatherByDay) \
#         .where(WeatherByDay.latitude == lake.latitude) \
#         .where(WeatherByDay.longitude == lake.longitude) \
#         .where(WeatherByDay.date.between(min_date, date))  # in_ function doesn;t wqork for dates for some reason
    
#     # print(statement.compile(engine))
    
#     weathers: list[WeatherByDay] = session.exec(statement).all()

#     # logger.warn(f"{weathers=}")
    
#     existing_weather_dates = [w.date for w in weathers]

#     # print(f"{existing_weather_dates=}")

#     weather_dates = [date - datetime.timedelta(days=x) for x in range(WEATHER_LOOKBACK_DAYS) ]
#     # logger.warn(f"{list(weather_dates)=}")
    
#     # If not all data is present, get it from the weather api and store it in the db
#     dates_to_get = []
#     for weather_date in weather_dates:
#         if weather_date not in existing_weather_dates:
#             dates_to_get.append(weather_date)

#     # logger.warn(f"{list(dates_to_get)=}")
    
#     if len(dates_to_get):
#         new_weathers = []
#         for d in dates_to_get:
#             new_weathers.append(
#                 get_weather_data(
#                     latitude=lake.latitude,
#                     longitude=lake.longitude,
#                     date=d
#                 )
#             )
            
#         # with Session(engine) as session:  # Will this error out if the primary keys arent unique?
#         #     session.add_all(new_weathers)
        
#         with engine.connect() as conn:
#             for wd in new_weathers:
#                 stmt = insert(WeatherByDay).values(wd.dict())
#                 stmt = stmt.on_conflict_do_nothing()  #left anti join for insert
#                 result = conn.execute(stmt)
#                 conn.commit()
                
#         # Add new weathers in
#         weathers += new_weathers

#     print("here")
#     print(weathers)

#     ice_thickness_m = get_ice_thickness(lake=lake, date=date, weather_reports_by_day=weathers)
        
#     CURRENT_ICE_ALG_VERSION = "0.0.1"

#     report = LakeFreezeReport(
#         lake_id=lake.id,
#         date=date,
#         ice_alg_version=CURRENT_ICE_ALG_VERSION,
#         ice_m=ice_thickness_m,
#         is_frozen=False
#     )

#     with engine.connect() as conn:
#         stmt = insert(LakeFreezeReport).values(report.dict())
#         stmt = stmt.on_conflict_do_nothing()
#         result = conn.execute(stmt)
#         conn.commit()

#     return report


def get_ice_thickness(lake: Lake, 
                      date: datetime.date,
                      weather_reports_by_day: list[WeatherByDay]
                      ) -> int:
    return 0.1



if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="localhost", port=8000, reload=True) 
    
handler = Mangum(app, lifespan="off")
