from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from sqlmodel import Session, select
from mangum import Mangum
import json
import boto3
from typing import Optional

from data_models import Lake
from database import engine

app = FastAPI()

# lakes = [
#     Lake(
#         "Bde Maka Ska",
#         "123",
#         44.9421125,
#         -93.3171757,
#         1620000.0,
#         9.1
#     ),
#     Lake(
#         "test",
#         "345",
#         0,
#         0,
#         1620000.0,
#         9.1
#     )
# ]


@app.get("/home", response_class=HTMLResponse)
def get_home_page():
    return """
    <html>
        <head>
            <title>Hello World</title>
        </head>
        <body>
         Hello World
        </body>
    </html>
    """


# @app.get("/lakes")
# def get_lakes(
#         min_surface_area: Optional[float] = None,
#         max_surface_area: Optional[float] = None,
#         min_latitude: float = -90.0,
#         max_latitude: float = 90.0,
#         min_longitude: float = -180.0,
#         max_longitude: float = 180.0
#     ):
    
#     # filtered_lakes = [
#     #     lake
#     #     for lake in lakes
#     #     if (
#     #         min_longitude <= lake.longitude <= max_longitude
#     #     ) and (
#     #         min_latitude <= lake.latitude <= max_latitude
#     #     )
#     # ]
    
#     with Session(engine) as session:
#         statement = select(Lake)
        
#         if min_surface_area:
#             statement = statement.where(Lake.surface_area_m2 >= min_surface_area)
        
#         if max_surface_area:
#             statement = statement.where(Lake.surface_area_m2 <= max_surface_area)
        
#         lakes = session.exec(statement.limit(10)).all()
#         print(lakes)

#     return lakes
    
    
handler = Mangum(app, lifespan="off")