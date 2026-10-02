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

    def list_by_context(self,context_id: int) -> list[AcousticMeasurement]:

        statement = (select(AcousticMeasurement)
                     .where(AcousticMeasurement.id_contexto == context_id)
                     .order_by(AcousticMeasurement.datetime))

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

    def sync_for_file(self,*,context_id: int, file_id: int, results: list[AcousticLevelResult]) -> list[AcousticMeasurement]:

        existing_measurements   = self.list_by_file(file_id)
        synced_measurements     = []
        existing                = {(measurement.datetime,measurement.aggregation_seconds):measurement for measurement in existing_measurements}
        seen_keys               = set()

        for result in results:

            key = (result.timestamp,result.aggregation_seconds)

            measurement = existing.get(key)

            if measurement is None:

                measurement = AcousticMeasurement(
                    id_contexto         = context_id,
                    id_archivo          = file_id,
                    datetime            = result.timestamp,
                    aggregation_seconds = result.aggregation_seconds
                )

                self.session.add(measurement)

            measurement.id_contexto = context_id
            measurement.id_archivo = file_id

            measurement.la_db = result.la_db
            measurement.lc_db = result.lc_db
            measurement.lz_db = result.lz_db
            measurement.la_max_db = result.la_max_db
            measurement.la_min_db = result.la_min_db
            measurement.lc_la_db = result.lc_la_db

            synced_measurements.append(measurement)
            seen_keys.add(key)

        for key,measurement in existing.items():

            if key not in seen_keys: self.session.delete(measurement)

        self.session.flush()

        return synced_measurements




