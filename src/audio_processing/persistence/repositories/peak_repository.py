from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from audio_processing.peaks.models import PeakResult
from audio_processing.persistence.models import  AcousticMeasurement, AcousticPeak,AcousticPeakMeasurement



class PeakRepository:

    def __init__(self,session: Session):
        self.session = session


    def sync_for_context(self,*,context_id: int, measurements: list[AcousticMeasurement],results: list[PeakResult]) -> tuple[list[AcousticPeak],list[AcousticPeakMeasurement]]:

        if not measurements: return [], []
        measurement_by_datetime = {}

        for measurement in measurements:

            if measurement.id_contexto != context_id: raise ValueError(f"Hay mediciones que no pertenecen al contexto {context_id}")

        
        for measurement in measurements:
            if measurement in measurement_by_datetime:raise ValueError(f"Existe mas de una medición para {measurement.datetime} dentro del conjunto seleccionado")
            measurement_by_datetime[measurement.datetime] = measurement
                
        measurement_ids = [measurement.id_medicion for measurement in measurements]
        
        statement = (select(AcousticPeak)
                        .where(AcousticPeak.id_contexto == context_id,
                               AcousticPeak.id_medicion_pico.in_(measurement_ids),))

        existing_rows = list(self.session.scalars(statement).all())
        existing = {row.id_medicion_pico: row for row in existing_rows}

        seen_measurement_ids = set()
        peak_rows = []

        for result in results:

            peak_measurement = measurement_by_datetime.get(result.peak_timestamp)

            if peak_measurement is None: raise ValueError(f"No existe una medición para el máximo del pico {result.peak_timestamp}")

            measurement_id = peak_measurement.id_medicion
            row = existing.get(measurement_id)

            if row is None: 
                row = AcousticPeak(id_contexto=context_id,id_medicion_pico=measurement_id)
                self.session.add(row)

            row.id_archivo_pico = peak_measurement.id_archivo
            row.datetime_pico = result.peak_timestamp
            row.start_time = result.start_time
            row.end_time = result.end_time
            row.duration_seconds = result.duration_seconds
            row.sample_count = result.sample_count
            row.peak_la_db = result.peak_la_db
            row.leq_db = result.leq_db
            row.prominence_db = result.prominence_db

            peak_rows.append(row)
            seen_measurement_ids.add(measurement_id)

        for measurement_id, row in existing.items():

            if measurement_id not in seen_measurement_ids: self.session.delete(row)

        self.session.flush()
        peak_ids = [row.id_pico for row in peak_rows]

        if peak_ids: 
            self.session.execute(delete(AcousticPeakMeasurement)
                                 .where(AcousticPeakMeasurement.id_pico.in_(peak_ids)))

        links = []

        for row,result in zip(peak_rows,results):

            for measurement in measurements:

                if result.start_time <= measurement.datetime <= result.end_time:
                    links.append(AcousticPeakMeasurement(id_pico = row.id_pico,id_medicion = measurement.id_medicion))


        self.session.add_all(links)
        self.session.flush()

        return (peak_rows,links)

    def list_apex_measurement_ids(self,*,context_id:int,measurement_ids:list[int]) -> set[int]:

        if not measurement_ids: return set()

        statement = (select(AcousticPeak.id_medicion_pico)
                     .where(
                         AcousticPeak.id_contexto == context_id,
                         AcousticPeak.id_medicion_pico.in_(measurement_ids)
                         )
                    )

        return set(self.session.scalars(statement).all())

