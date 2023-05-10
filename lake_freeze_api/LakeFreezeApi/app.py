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

from data_models import Lake, WeatherByDay, LakeFreezeReport
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
            
    with Session(engine) as session:
        statement = select(Lake)

        if id:
            statement = statement.where(Lake.id == id)
        
        if min_surface_area:
            statement = statement.where(Lake.surface_area_m2 >= min_surface_area)
        
        if max_surface_area:
            statement = statement.where(Lake.surface_area_m2 <= max_surface_area)
        
        statement = statement.limit(limit)
        
        lakes = session.exec(statement).all()

    response.headers.update(cors_headers)

    return lakes
    

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

def insert_lake_freeze_report(report: LakeFreezeReport):
    with engine.connect() as conn:
        stmt = insert(LakeFreezeReport).values(report.dict())
        stmt = stmt.on_conflict_do_nothing()
        result = conn.execute(stmt)
    conn.commit()


@app.get("/lake_weather_reports/")
def get_lake_weather_reports(
        lake_id: Annotated[list[int], Query()],
        date: datetime.date = datetime.datetime.today().date(),
        background_tasks: BackgroundTasks = None # Used for writing to DB after the response is returned
    )-> list[LakeFreezeReport]:


    lake_ids = lake_id  # Renaming for clarity

    logger = logging.getLogger()

    logger.setLevel(logging.INFO)
            
    WEATHER_LOOKBACK_DAYS = 7

    min_date = date - datetime.timedelta(days=WEATHER_LOOKBACK_DAYS)
    

    lakes: list[Lake] = []
    with Session(engine) as session:
        for lake_id in lake_ids:
            lakes.append(
                session.get(Lake, lake_id)
            )

    logger.setLevel(logging.INFO)
    # logger.warn(f"{lake=}")

    # TODO this probably should just be a sql join
        
    stmt = select(WeatherByDay)
    
    stmt = stmt.where(
        functools.reduce(or_,
            [
                and_(WeatherByDay.latitude == lake.latitude, WeatherByDay.longitude == lake.longitude ) 
                for lake in lakes
            ]
        )
    )

    stmt = stmt.where(WeatherByDay.date.between(min_date, date))

    # statement = select(WeatherByDay) \
    #     .where(WeatherByDay.latitude == lake.latitude) \
    #     .where(WeatherByDay.longitude == lake.longitude) \
    #     .where(WeatherByDay.date.between(min_date, date))  # in_ function doesn;t wqork for dates for some reason
    
    # print(statement.compile(engine))
    
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

    logger.warn(f"{list(weathers_to_get)=}")
    

    new_weathers = []
    for weather in weathers_to_get:
        new_weathers.append(
            get_weather_data(
                **weather
            )
        )
    
    background_tasks.add_task(insert_weathers, new_weathers)
            
    # Add new weathers in
    weathers = existing_weathers + new_weathers

        
    CURRENT_ICE_ALG_VERSION = "0.0.1"

    print(lakes)

    reports = []
    for lake in lakes:
        weathers_for_lake = []
        for weather in weathers:
            if lake.latitude == weather.latitude and lake.longitude == weather.longitude:
                if weather.date not in [w.date for w in weathers_for_lake]:
                    weathers_for_lake.append(weather)

        ice_thickness_m = ashton_ice_growth(weathers_for_lake)

        
        print(ice_thickness_m)

        report = LakeFreezeReport(
            lake_id=lake.id,
            date=date,
            ice_alg_version=CURRENT_ICE_ALG_VERSION,
            ice_m=ice_thickness_m,
            is_frozen=ice_thickness_m > 0
        )

        reports.append(report)

    print(reports)

    # background_tasks.add_task(insert_lake_freeze_report, report)    

    return reports





if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="localhost", port=8000, reload=True) 
    
handler = Mangum(app, lifespan="off")
