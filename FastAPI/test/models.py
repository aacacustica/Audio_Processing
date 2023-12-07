from sqlalchemy import Column, Integer, String, Date
from .database import Base

class Sensor(Base):
    __tablename__ = "Sensor"

    SensorlD = Column(Integer, primary_key=True, index=True)
    SensorName = Column(String)
    Location = Column(String)
    DateObserved = Column(Date)
    HeightAverage = Column(String)
    SonometerClass = Column(String)
    RefWeatherObserved = Column(String)
