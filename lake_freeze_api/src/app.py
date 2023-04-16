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
        min_latitude: float = -90.0,
        max_latitude: float = 90.0,
        min_longitude: float = -180.0,
        max_longitude: float = 180.0
    ):
    
    filtered_lakes = [
        lake
        for lake in lakes
        if (
            min_longitude <= lake.longitude <= max_longitude
        ) and (
            min_latitude <= lake.latitude <= max_latitude
        )
    ]

    return filtered_lakes