from typing import Annotated
import functools

from fastapi import FastAPI, BackgroundTasks, Response, Query
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware

from sqlmodel import Session, select
from sqlalchemy.sql.operators import is_, or_, and_
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import cast, Numeric, Float
import sqlalchemy
from mangum import Mangum
import json
import boto3
from typing import Optional, Any
import datetime

from data_models import DailyWeather, WaterBody, WaterBodyGeometry, WaterBodyWeatherReport
from weather_api import get_weather_data
from ice_growth_models import ashton_ice_growth

import sys

sys.setrecursionlimit(10000)# It sets recursion limit to 10000.


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


@app.get("/water_bodies")
def get_water_bodies(
        response: Response,
        id: Optional[int] = None,
        min_surface_area: Optional[float] = None,
        max_surface_area: Optional[float] = None,
        min_latitude: float = -90.0,
        max_latitude: float = 90.0,
        min_longitude: float = -180.0,
        max_longitude: float = 180.0,
        limit: int = 100   

    ) -> list[WaterBody]:
    # WaterBody
    ids = [id] if id is not None else None
    water_bodies = query_water_bodies(**locals())

    response.headers.update(cors_headers) #TODO is this necessary?
    return water_bodies

def query_water_bodies(
        ids: list[str] = None,
        min_surface_area: Optional[float] = None,
        max_surface_area: Optional[float] = None,
        min_latitude: float = -90.0,
        max_latitude: float = 90.0,
        min_longitude: float = -180.0,
        max_longitude: float = 180.0,
        limit: int = 100,
        order_by_size: bool = True,
        **kwargs
    ) -> list[WaterBody]:
    with Session(engine) as session:
        statement = select(WaterBody)

        if ids:
            statement = statement.filter(WaterBody.id.in_(ids))
        
        if min_surface_area:
            statement = statement.where(WaterBody.areasqkm >= min_surface_area)
        
        if max_surface_area:
            statement = statement.where(WaterBody.areasqkm <= max_surface_area)

        statement = (
            statement
                .where(cast(WaterBody.latitude , Float)>= min_latitude)
                .where(cast(WaterBody.latitude , Float)<= max_latitude)
                .where(cast(WaterBody.longitude, Float) >= min_longitude)
                .where(cast(WaterBody.longitude, Float) <= max_longitude)
        )
    
        if order_by_size:
            statement = statement.order_by(WaterBody.areasqkm.desc())

        statement = statement.limit(limit)
        
        water_bodies = session.exec(statement).all()

    return water_bodies


@app.get("/water_body_geometries")
def get_water_bodies(
        response: Response,
        water_body_ids: Optional[str] = None

    ) -> list[Any]:

    if water_body_ids:
        water_body_ids = str(water_body_ids).split(",")  # Renaming for clarity

    with Session(engine) as session:
        statement = select(WaterBodyGeometry).filter(WaterBodyGeometry.id.in_(water_body_ids))

        water_body_geometries = session.exec(statement).all()

    response.headers.update(cors_headers) #TODO is this necessary?
    return water_body_geometries



# TODO add water_body size sorting for limit
@app.get("/water_body_weather_reports/")
def get_water_body_weather_reports(
        date: datetime.date = datetime.datetime.today().date(),
        # water_body_id: Annotated[list[int], Query()] = None,
        water_body_ids: str = None, # comma separated list of water_body ids
        min_surface_area: Optional[float] = None,
        max_surface_area: Optional[float] = None,
        min_latitude: float = -90.0,
        max_latitude: float = 90.0,
        min_longitude: float = -180.0,
        max_longitude: float = 180.0,
        limit: int = 100,
        background_tasks: BackgroundTasks = None, # Used for writing to DB after the response is returned
        response: Response = None
    ) -> list[WaterBodyWeatherReport]:

    if water_body_ids:
        water_body_ids = water_body_ids.split(",")  # Renaming for clarity

    # print(f"{water_body_ids}")

    water_bodys = query_water_bodies(**locals())

    logger = logging.getLogger()

    logger.setLevel(logging.INFO)
            
    WEATHER_LOOKBACK_DAYS = 7 #365

    min_date = date - datetime.timedelta(days=WEATHER_LOOKBACK_DAYS)
    
    # latlong_filter = ' OR '.join([f"(latitude = {water_body.latitude} AND longitude = {water_body.longitude} )" for water_body in water_bodys])

    # engine.execute(f"""
    # SELECT * FROM {DailyWeather.__tablename__}
    # WHERE
    # (
    #     {latlong_filter}
    # )
    # AND date BETWEEN {min_date} AND {date}
    # """)


    # TODO this probably should just be a sql join
    
    with Session(engine) as session:
        stmt = select(DailyWeather)
        
        if len(water_bodys):
            stmt = stmt.where(
                functools.reduce(or_,
                    [
                        and_(DailyWeather.latitude == water_body.latitude, DailyWeather.longitude == water_body.longitude ) 
                        for water_body in water_bodys
                    ]
                )
            )

        stmt = stmt.where(DailyWeather.date.between(min_date, date))

        existing_weathers: list[DailyWeather] = session.exec(stmt).all()

    logger.warn(f"{existing_weathers=}")
    
    # existing_weather_dates = [w.date for w in weathers]

    # print(f"{existing_weather_dates=}")

    weather_dates = [date - datetime.timedelta(days=x) for x in range(WEATHER_LOOKBACK_DAYS) ]
    # logger.warn(f"{list(weather_dates)=}")
    
    # If not all data is present, get it from the weather api and store it in the db
    weathers_to_get = []
    
    for water_body in water_bodys:
        for weather_date in weather_dates:
            has_existing_weather = False
            for weather in existing_weathers:
                if (weather.date == weather_date 
                    and water_body.latitude == weather.latitude 
                    and water_body.longitude == weather.longitude
                ):
                    has_existing_weather = True
            if not has_existing_weather:
                weathers_to_get.append({
                        "latitude": water_body.latitude,
                        "longitude": water_body.longitude,
                        "date": weather_date
                    })


            # if weather_date not in existing_weather_dates:
            #     dates_to_get.append(weather_date)

    logger.warn(f"{list(weathers_to_get)=}")
    
    from concurrent.futures import ThreadPoolExecutor

    # new_weathers = []
    # with ThreadPoolExecutor(max_workers=500) as executor:
    #     futures = []
    #     for weather in weathers_to_get:
    #         futures.append(
    #             executor.submit(get_weather_data, **weather)
    #         )

    #     for future in futures:
    #         try:
    #             new_weathers.append(
    #                 future.result()
    #             )
    #         except Exception as e:
    #             print(e)
    
    # background_tasks.add_task(insert_weathers, new_weathers)
            
    # Add new weathers in
    weathers = existing_weathers #+ new_weathers

        
    CURRENT_ICE_ALG_VERSION = "0.0.1"

    # print(water_bodys)

    reports = []
    for water_body in water_bodys:
        weathers_for_water_body = []
        for weather in weathers:
            if water_body.latitude == weather.latitude and water_body.longitude == weather.longitude:
                if weather.date not in [w.date for w in weathers_for_water_body]:
                    weathers_for_water_body.append(weather)

        ice_thickness_m = ashton_ice_growth(weathers_for_water_body)

        
        # print(ice_thickness_m)

        report = WaterBodyWeatherReport(
            water_body_id=water_body.id,
            date=date,
            ice_alg_version=CURRENT_ICE_ALG_VERSION,
            ice_m=ice_thickness_m,
            is_frozen=ice_thickness_m > 0,
            latitude=water_body.latitude,
            longitude=water_body.longitude,
            water_body_name=water_body.name
        )

        reports.append(report)

    # print(reports)

    # background_tasks.add_task(insert_water_body_freeze_report, report)    

    return reports


# @app.get("/water_bodys/update_lat_long")
# def update_lat_long(
#         limit: int = 1
#     ):
#     with Session(engine) as session:
#         statement = select(Lake).where(Lake.longitude.is_(None) | Lake.latitude.is_(None)).limit(limit)
#         water_bodys = session.exec(statement).all()

#     update_latitude_and_longitude(water_bodys)

#     return f"updated {len(water_bodys)}"
    

def insert_weathers(weathers: list[DailyWeather]):
    with engine.connect() as conn:
        for wd in weathers:
            stmt = insert(DailyWeather).values(wd.dict())
            stmt = stmt.on_conflict_do_nothing()  #left anti join for insert
            result = conn.execute(stmt)
        conn.commit()

def insert_water_body_freeze_report(report: WaterBodyWeatherReport):
    with engine.connect() as conn:
        stmt = insert(WaterBodyWeatherReport).values(report.dict())
        stmt = stmt.on_conflict_do_nothing()
        result = conn.execute(stmt)
    conn.commit()



if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="localhost", port=8000, reload=True) 
    
handler = Mangum(app, lifespan="off")
