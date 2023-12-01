from sqlalchemy.orm import Session
import models, schemas

def get_sensors(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Sensor).offset(skip).limit(limit).all()

def get_noise_readings(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.NoiseReading1s).offset(skip).limit(limit).all()

def get_daily_indicators(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.DailyIndicator).offset(skip).limit(limit).all()

def get_sound_events(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.SoundEvent).offset(skip).limit(limit).all()

def get_aggregate_readings(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.AggregateReading).offset(skip).limit(limit).all()