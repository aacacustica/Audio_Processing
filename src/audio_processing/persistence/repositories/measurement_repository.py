from datetime import datetime

from sqlalchemy import select,delete
from sqlalchemy.orm import Session

from audio_processing.persistence.models import AcousticMeasurement
from audio_processing.spl.models import AcousticLevelResult


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

    def add_many(self,*,context_id:int,file_id: int | None, results: list[AcousticLevelResult]) -> list[AcousticMeasurement]:

        measurements = [ AcousticMeasurement(
            id_contexto = context_id,
            id_archivo = file_id,
            datetime = result.timestamp,
            aggregation_seconds = result.aggregation_seconds,
            la_db = result.la_db,
            lc_db = result.lc_db,
            lz_db = result.lz_db,
            la_max_db = result.la_max_db,
            la_min_db = result.la_min_db,
            lc_la_db = result.lc_la_db
            ) for result in results
        ]

        self.session.add_all(measurements)
        self.session.flush()

        return measurements

    def replace_for_file(self,*,context_id: int,file_id: int,results: list[AcousticLevelResult]) -> list[AcousticMeasurement]:

        self.session.execute(
            delete(AcousticMeasurement)
            .where(AcousticMeasurement.id_archivo == file_id)
        )

        measurements = [ AcousticMeasurement(
                    id_contexto = context_id,
                    id_archivo = file_id,
                    datetime = result.timestamp,
                    aggregation_seconds = result.aggregation_seconds,
                    la_db = result.la_db,
                    lc_db = result.lc_db,
                    lz_db = result.lz_db,
                    la_max_db = result.la_max_db,
                    la_min_db = result.la_min_db,
                    lc_la_db = result.lc_la_db
                    ) for result in results
        ]

        self.session.add_all(measurements)
        self.session.flush()

        return measurements

