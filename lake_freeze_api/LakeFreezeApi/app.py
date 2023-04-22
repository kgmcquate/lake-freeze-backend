from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from sqlmodel import Session, select
from sqlalchemy.dialects.postgresql import insert
from mangum import Mangum
import json
import boto3
from typing import Optional
import datetime

from data_models import Lake, WeatherByDay
from external_api_calls import get_weather_data

app = FastAPI()

from database import engine


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
        
    print("creating session")
    
    with Session(engine) as session:
        statement = select(Lake)
        
        if min_surface_area:
            statement = statement.where(Lake.surface_area_m2 >= min_surface_area)
        
        if max_surface_area:
            statement = statement.where(Lake.surface_area_m2 <= max_surface_area)
        print("executing statement")
        
        statement = statement.limit(limit)
        
        lakes = session.exec(statement).all()
        print("executed statement")
        print(lakes)

    return lakes
    
    

@app.get("/lake_freeze_reports")
def get_lake_freeze_reports(
        lake_id: int, 
        date: datetime.date = datetime.datetime.today().date()
    ) -> list[WeatherByDay]:
            
    WEATHER_LOOKBACK_DAYS = 30
    
    weather_dates = (date - datetime.timedelta(days=x) for x in range(WEATHER_LOOKBACK_DAYS) )
    
    with Session(engine) as session:
        lake: Lake = session.get(Lake, lake_id)
        
        
    statement = select(WeatherByDay) \
        .where(WeatherByDay.latitude == lake.latitude and WeatherByDay.longitude == lake.longitude) \
        .where(WeatherByDay.date in weather_dates)
    
    weathers: list[WeatherByDay] = session.exec(statement).all()
    
    existing_weather_dates = [w.date for w in weathers]
    
    # If not all data is present, get it from the weather api and store it in the db
    dates_to_get = []
    for weather_date in weather_dates:
        if weather_date not in existing_weather_dates:
            dates_to_get.append(weather_date)
    
    if len(dates_to_get):
        new_weathers = []
        for d in dates_to_get:
            new_weathers.append(
                get_weather_data()
            )
            
        # with Session(engine) as session:  # Will this error out if the primary keys arent unique?
        #     session.add_all(new_weathers)
        
        with engine.connect() as conn:
            for wd in new_weathers:
                stmt = insert(WeatherByDay).values(wd.dict())
                stmt = stmt.on_conflict_do_nothing()  #left anti join for insert
                result = conn.execute(stmt)
                conn.commit()
                
        # Add new weathers in
        weathers += new_weathers
        
    return weathers

    
    
handler = Mangum(app, lifespan="off")
