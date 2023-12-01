from sqlalchemy.orm import Session
from . import models, schemas

def get_sensors(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Sensor).offset(skip).limit(limit).all()