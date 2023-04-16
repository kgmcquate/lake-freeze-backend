from pydantic.dataclasses import dataclass

@dataclass
class Lake:
    name: str
    id: str
    latitude: float
    longitude: float
    surface_area_sq_meters: float
    avg_depth_meters: float
    