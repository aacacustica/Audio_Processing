from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from audio_processing.persistence.models import AcousticMeasurement


class MeasurementRepository:

    def __init__(self,session:Session):
        self.session = session


    def add(self,*,context_id,file_id: int | None, timestamp: datetime, aggregation_seconds: float, la_db: float | None,lc_db: float | None,lz_db: float | None,la_max_db: float | None,la_min_db: float | None,lc_la_db: float | None) -> AcousticMeasurement:

        measurement = AcousticMeasurement(
            id_contexto         = context_id,
            id_archivo          = file_id,
            datetime            = timestamp,
            aggregation_seconds = aggregation_seconds,
            la_db               = la_db,
            lc_db               = lc_db,
            lz_db               = lz_db,
            la_max_db           = la_max_db,
            la_min_db           = la_min_db,
            lc_la_db            = lc_la_db
        )

        self.session.add(measurement)
        self.session.flush()

        return measurement


    def list_by_file(self,file_id: int) -> list[AcousticMeasurement]:

        statement = (
            select(AcousticMeasurement)
            .where( AcousticMeasurement.id_archivo == file_id )
            .order_by( AcousticMeasurement.datetime )
        )

        return list(self.session.scalars(statement).all())
        