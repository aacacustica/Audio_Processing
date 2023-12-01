from pydantic import BaseModel
from typing import List
from typing import Optional
from datetime import datetime
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

class NoiseReading1sBase(BaseModel):
    SensorID: int
    LAeq: str
    LAmax: str
    Band100Hz: str
    Band125Hz: str
    Band160Hz: str
    Band200Hz: str
    Band250Hz: str
    Band315Hz: str
    Band400Hz: str
    Band500Hz: str
    Band630Hz: str
    Band800Hz: str
    Band1kHz: str
    Band1_25kHz: str
    Band1_6kHz: str
    Band2kHz: str
    Band2_5kHz: str
    Band3_15kHz: str
    Band4kHz: str
    Band5kHz: str
    ReadingDateTime: datetime

class NoiseReading1s(NoiseReading1sBase):
    ReadingID: int

    class Config:
        orm_mode = True


class DailyIndicatorBase(BaseModel):
    LD: str
    LN: str
    LE: str
    LDEN: str
    Date: date

class DailyIndicator(DailyIndicatorBase):
    IndicatorID: int
    SensorID: int

    class Config:
        orm_mode = True


class SoundEventBase(BaseModel):
    StartDateTime: date
    EndDateTime: date
    SELLevel: Optional[str] = None
    MaxLevel: Optional[str] = None
    Prediction: Optional[str] = None

class SoundEvent(SoundEventBase):
    EventID: int
    SensorID: int

    class Config:
        orm_mode = True


class AggregateReadingBase(BaseModel):
    LAeq_T: str
    Percentile10: Optional[str] = None
    Percentile50: Optional[str] = None
    Percentile90: Optional[str] = None
    AggregateStartDateTime: date
    AggregateEndDateTime: date

class AggregateReading(AggregateReadingBase):
    AggregateID: int
    SensorID: int

    class Config:
        orm_mode = True




""""
#############
# STRUCTURE #
#############
 
class SensorBase(BaseModel):
    name: str
    # Add other fields

class Sensor(SensorBase):
    id: int

    class Config:
        orm_mode = True
"""