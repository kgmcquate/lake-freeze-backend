from fastapi import FastAPI
from .orm_dataclasses import Lake

app = FastAPI()

lakes = [
    Lake(
        "Bde Maka Ska",
        "123",
        44.9421125,
        -93.3171757,
        1620000.0,
        9.1
    ),
    Lake(
        "test",
        "345",
        0,
        0,
        1620000.0,
        9.1
    )
]


@app.get("/lakes")
def get_lakes(
        start_latitude: float = -90.0,
        end_latitude: float = 90.0,
        start_longitude: float = -180.0,
        end_longitude: float = 180.0
    ):
    
    filtered_lakes = [
        lake
        for lake in lakes
        if (
            start_longitude <= lake.longitude <= end_longitude
        ) and (
            start_latitude <= lake.latitude <= end_latitude
        )
    ]

    return filtered_lakes