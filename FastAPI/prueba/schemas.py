from pydantic import BaseModel
from typing import Optional
from datetime import date

class SensorBase(BaseModel):
    SensorName: str
    Location: str
    DateObserved: date
    HeightAverage: Optional[str] = None
    SonometerClass: Optional[str] = None
    RefWeatherObserved: Optional[str] = None

class Sensor(SensorBase):
    SensorlD: int

    class Config:
        orm_mode = True