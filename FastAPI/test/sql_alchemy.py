from sqlalchemy import Column, Integer, String, Date, ForeignKey, TIMESTAMP
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Sensor(Base):
    __tablename__ = "sensor"
    
    SensorID = Column(Integer, primary_key=True)
    SensorName = Column(String)
    Location = Column(String)
    DateObserved = Column(Date)
    HeightAverage = Column(String)
    SonometerClass = Column(String)
    RefWeatherObserved = Column(String)

    readings = relationship('NoiseReading1s', back_populates='sensor')
    events = relationship('SoundEvent', back_populates='sensor')
    indicators = relationship('DailyIndicator', back_populates='sensor')
    aggregates = relationship('AggregateReading', back_populates='sensor')

class NoiseReading1s(Base):
    __tablename__ = "noise_reading1s"
    
    ReadingID = Column(Integer, primary_key=True)
    SensorID = Column(Integer, ForeignKey('sensor.SensorID'))
    LAeq = Column(String)
    LAmax = Column(String)
    Band100Hz = Column(String)
    Band125Hz = Column(String)
    Band160Hz = Column(String)
    Band200Hz = Column(String)
    Band250Hz = Column(String)
    Band315Hz = Column(String)
    Band400Hz = Column(String)
    Band500Hz = Column(String)
    Band630Hz = Column(String)
    Band800Hz = Column(String)
    Band1000Hz = Column(String)
    Band1025Hz = Column(String)
    Band1600Hz = Column(String)
    Band2000Hz = Column(String)
    Band2500Hz = Column(String)
    Band3150Hz = Column(String)
    Band4000Hz = Column(String)
    ReadingDateTime = Column(TIMESTAMP)
    
    sensor = relationship('Sensor', back_populates='readings')

class SoundEvent(Base):
    __tablename__ = "sound_event"
    
    EventID = Column(Integer, primary_key=True)
    SensorID = Column(Integer, ForeignKey('sensor.SensorID'))
    StartDateTime = Column(TIMESTAMP)
    EndDateTime = Column(TIMESTAMP)
    SELLevel = Column(String)
    MaxLevel = Column(String)
    Prediction = Column(String)

    sensor = relationship('Sensor', back_populates='events')

class DailyIndicator(Base):
    __tablename__ = "daily_indicator"
    
    IndicatorID = Column(Integer, primary_key=True)
    SensorID = Column(Integer, ForeignKey('sensor.SensorID'))
    LD = Column(String)
    LN = Column(String)
    LE = Column(String)
    LDEN = Column(String)
    Date = Column(Date)

    sensor = relationship('Sensor', back_populates='indicators')

class AggregateReading(Base):
    __tablename__ = "aggregate_reading"
    
    AggregateID = Column(Integer, primary_key=True)
    SensorID = Column(Integer, ForeignKey('sensor.SensorID'))
    LAeq_T = Column(String)
    Percentile10 = Column(String)
    Percentile50 = Column(String)
    Percentile90 = Column(String)
    AggregateStartDateTime = Column(TIMESTAMP)
    AggregateEndDateTime = Column(TIMESTAMP)

    sensor = relationship('Sensor', back_populates='aggregates')