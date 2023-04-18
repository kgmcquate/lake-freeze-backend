from typing import Optional
from sqlmodel import Field, Session, SQLModel
from database import engine

# @dataclass
# class Lake:
#     name: str
#     nearby_town: str
#     # id: str
#     # latitude: float
#     # longitude: float
#     surface_area_m2: float
#     avg_depth_m: float
    
    

class Lake(SQLModel, table=True):
    __tablename__ = "lakes"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    nearby_town: str
    # id: str
    # latitude: float
    # longitude: float
    surface_area_m2: float
    max_depth_m: float
    
# SQLModel.metadata.create_all(engine)

# with Session(database.engine) as session:
#     session.add(hero_1)
#     session.add(hero_2)
#     session.add(hero_3)
#     session.commit()