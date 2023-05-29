from typing import Annotated
import functools

from fastapi import FastAPI, BackgroundTasks, Response, Query
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware

from sqlmodel import Session, select
from sqlalchemy.sql.operators import is_, or_, and_
from sqlalchemy.dialects.postgresql import insert
from mangum import Mangum
import json
import boto3
from typing import Optional
import datetime

from data_models import Lake, WeatherByDay, LakeWeatherReport
from weather_api import get_weather_data
from google_maps_api import update_latitude_and_longitude
from ice_growth_models import ashton_ice_growth

app = FastAPI()


origins = [
    "*"
    # "http://localhost.tiangolo.com",
    # "https://localhost.tiangolo.com",
    # "http://localhost",
    # "http://localhost:8080",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

cors_headers = {
            "Access-Control-Allow-Headers" : "Content-Type,X-Amz-Date,Authorization,X-Api-Key,x-requested-with",
            "Access-Control-Allow-Origin": "*", # Allow from anywhere 
            "Access-Control-Allow-Methods": "*" # Allow only GET request 
        }

from database import engine

import logging

from sqlmodel import SQLModel
SQLModel.metadata.create_all(engine)


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
        response: Response,
        id: Optional[int] = None,
        min_surface_area: Optional[float] = None,
        max_surface_area: Optional[float] = None,
        min_latitude: float = -90.0,
        max_latitude: float = 90.0,
        min_longitude: float = -180.0,
        max_longitude: float = 180.0,
        limit: int = 100        
    ):

    lakes = query_lakes(**locals())

    response.headers.update(cors_headers) #TODO is this necessary?
    return lakes

            
def query_lakes(
        lake_ids: list[str] = None,
        min_surface_area: Optional[float] = None,
        max_surface_area: Optional[float] = None,
        min_latitude: float = -90.0,
        max_latitude: float = 90.0,
        min_longitude: float = -180.0,
        max_longitude: float = 180.0,
        limit: int = 100,
        order_by_size: bool = True,
        **kwargs
    ):

    # id_filter = "true" if lake_ids is None else f"id IN ({','.join(lake_ids)})"

    # rows = engine.execute(f"""
    # SELECT * FROM {Lake.__tablename__}
    # WHERE 
    #     {id_filter}
    #     AND
    #     latitude >= {min_latitude}
    #     AND
    #     latitude <= {max_latitude}
    #     AND
    #     longitude >= {min_longitude}
    #     AND
    #     longitude <= {max_longitude}
    # LIMIT {limit}
    # """)

    # lakes = (Lake(**row) for row in rows)

    with Session(engine) as session:
        statement = select(Lake)

        if lake_ids:
            statement = statement.filter(Lake.id.in_(lake_ids))
        
        if min_surface_area:
            statement = statement.where(Lake.surface_area_m2 >= min_surface_area)
        
        if max_surface_area:
            statement = statement.where(Lake.surface_area_m2 <= max_surface_area)
        
        statement = (
            statement
                .where(Lake.latitude >= min_latitude)
                .where(Lake.latitude <= max_latitude)
                .where(Lake.longitude >= min_longitude)
                .where(Lake.longitude <= max_longitude)
        )
    
        if order_by_size:
            statement = statement.order_by(Lake.surface_area_m2.desc())

        statement = statement.limit(limit)
        
        lakes = session.exec(statement).all()

    return lakes
    

# TODO add lake size sorting for limit
@app.get("/lake_weather_reports/")
def get_lake_weather_reports(
        date: datetime.date = datetime.datetime.today().date(),
        # lake_id: Annotated[list[int], Query()] = None,
        lake_ids: str = None, # comma separated list of lake ids
        min_surface_area: Optional[float] = None,
        max_surface_area: Optional[float] = None,
        min_latitude: float = -90.0,
        max_latitude: float = 90.0,
        min_longitude: float = -180.0,
        max_longitude: float = 180.0,
        limit: int = 100,
        background_tasks: BackgroundTasks = None, # Used for writing to DB after the response is returned
        response: Response = None
    ) -> list[LakeWeatherReport]:

    if lake_ids:
        lake_ids = lake_ids.split(",")  # Renaming for clarity

    # print(f"{lake_ids}")

    lakes = query_lakes(**locals())

    logger = logging.getLogger()

    logger.setLevel(logging.INFO)
            
    WEATHER_LOOKBACK_DAYS = 7

    min_date = date - datetime.timedelta(days=WEATHER_LOOKBACK_DAYS)
    
    # latlong_filter = ' OR '.join([f"(latitude = {lake.latitude} AND longitude = {lake.longitude} )" for lake in lakes])

    # engine.execute(f"""
    # SELECT * FROM {WeatherByDay.__tablename__}
    # WHERE
    # (
    #     {latlong_filter}
    # )
    # AND date BETWEEN {min_date} AND {date}
    # """)


    # TODO this probably should just be a sql join
    
    with Session(engine) as session:
        stmt = select(WeatherByDay)
        
        if len(lakes):
            stmt = stmt.where(
                functools.reduce(or_,
                    [
                        and_(WeatherByDay.latitude == lake.latitude, WeatherByDay.longitude == lake.longitude ) 
                        for lake in lakes
                    ]
                )
            )

        stmt = stmt.where(WeatherByDay.date.between(min_date, date))

        existing_weathers: list[WeatherByDay] = session.exec(stmt).all()

    # logger.warn(f"{weathers=}")
    
    # existing_weather_dates = [w.date for w in weathers]

    # print(f"{existing_weather_dates=}")

    weather_dates = [date - datetime.timedelta(days=x) for x in range(WEATHER_LOOKBACK_DAYS) ]
    # logger.warn(f"{list(weather_dates)=}")
    
    # If not all data is present, get it from the weather api and store it in the db
    weathers_to_get = []
    
    for lake in lakes:
        for weather_date in weather_dates:
            has_existing_weather = False
            for weather in existing_weathers:
                if (weather.date == weather_date 
                    and lake.latitude == weather.latitude 
                    and lake.longitude == weather.longitude
                ):
                    has_existing_weather = True
            if not has_existing_weather:
                weathers_to_get.append({
                        "latitude": lake.latitude,
                        "longitude": lake.longitude,
                        "date": weather_date
                    })


            # if weather_date not in existing_weather_dates:
            #     dates_to_get.append(weather_date)

    # logger.warn(f"{list(weathers_to_get)=}")
    
    from concurrent.futures import ThreadPoolExecutor

    new_weathers = []
    with ThreadPoolExecutor(max_workers=500) as executor:
        futures = []
        for weather in weathers_to_get:
            futures.append(
                executor.submit(get_weather_data, **weather)
            )

        for future in futures:
            try:
                new_weathers.append(
                    future.result()
                )
            except Exception as e:
                print(e)
    
    background_tasks.add_task(insert_weathers, new_weathers)
            
    # Add new weathers in
    weathers = existing_weathers + new_weathers

        
    CURRENT_ICE_ALG_VERSION = "0.0.1"

    # print(lakes)

    reports = []
    for lake in lakes:
        weathers_for_lake = []
        for weather in weathers:
            if lake.latitude == weather.latitude and lake.longitude == weather.longitude:
                if weather.date not in [w.date for w in weathers_for_lake]:
                    weathers_for_lake.append(weather)

        ice_thickness_m = ashton_ice_growth(weathers_for_lake)

        
        # print(ice_thickness_m)

        report = LakeWeatherReport(
            lake_id=lake.id,
            date=date,
            ice_alg_version=CURRENT_ICE_ALG_VERSION,
            ice_m=ice_thickness_m,
            is_frozen=ice_thickness_m > 0,
            latitude=lake.latitude,
            longitude=lake.longitude,
            lake_name=lake.lake_name
        )

        reports.append(report)

    # print(reports)

    # background_tasks.add_task(insert_lake_freeze_report, report)    

    return reports


@app.get("/lakes/update_lat_long")
def update_lat_long(
        limit: int = 1
    ):
    with Session(engine) as session:
        statement = select(Lake).where(Lake.longitude.is_(None) | Lake.latitude.is_(None)).limit(limit)
        lakes = session.exec(statement).all()

    update_latitude_and_longitude(lakes)

    return f"updated {len(lakes)}"
    

def insert_weathers(weathers: list[WeatherByDay]):
    with engine.connect() as conn:
        for wd in weathers:
            stmt = insert(WeatherByDay).values(wd.dict())
            stmt = stmt.on_conflict_do_nothing()  #left anti join for insert
            result = conn.execute(stmt)
        conn.commit()

def insert_lake_freeze_report(report: LakeWeatherReport):
    with engine.connect() as conn:
        stmt = insert(LakeWeatherReport).values(report.dict())
        stmt = stmt.on_conflict_do_nothing()
        result = conn.execute(stmt)
    conn.commit()



if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="localhost", port=8000, reload=True) 
    
handler = Mangum(app, lifespan="off")
