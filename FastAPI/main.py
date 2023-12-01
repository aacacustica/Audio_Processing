from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from database import SessionLocal, engine
from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List
import crud, models, schemas
# send request
from fastapi import UploadFile, File
from pydantic import BaseModel

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/sensors", response_model=List[schemas.Sensor])
def read_sensors(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    sensors = crud.get_sensors(db, skip=skip, limit=limit)
    return sensors

@app.get("/noise_readings", response_model=List[schemas.NoiseReading1s])
def read_noise_readings(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    readings = crud.get_noise_readings(db, skip=skip, limit=limit)
    return readings

@app.get("/daily_indicators", response_model=List[schemas.DailyIndicator])
def read_daily_indicators(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    indicators = crud.get_daily_indicators(db, skip=skip, limit=limit)
    return indicators

@app.get("/sound_events", response_model=List[schemas.SoundEvent])
def read_sound_events(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    events = crud.get_sound_events(db, skip=skip, limit=limit)
    return events

@app.get("/aggregate_readings", response_model=List[schemas.AggregateReading])
def read_aggregate_readings(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    aggregates = crud.get_aggregate_readings(db, skip=skip, limit=limit)
    return aggregates

# Send file
@app.post("/uploadaudio/")
async def upload_audio(file: UploadFile = File(...)):
    file_contents = await file.read()
    # file_contents contains the contents of the uploaded file
    # We can process this data as needed
    # For example, we can save the file to disk:
    with open(file.filename, 'wb') as f:
        f.write(file_contents)

    return {"filename": file.filename}
