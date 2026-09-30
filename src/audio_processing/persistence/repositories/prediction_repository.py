import datetime

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from audio_processing.ai.models import PredictionResult
from audio_processing.persistence.models import AcousticMeasurement,AIPrediction,AIPredictionMeasurement


class PredictionRepository:

    def __init__(self,session: Session):
        self.session = session


    def sync_for_file(self,*,file_id:int,measurements:list[AcousticMeasurement],results: list[PredictionResult],model_name:str,threshold:float) -> tuple[list[AIPrediction],list[AIPredictionMeasurement]]:

        statement = (
            select(AIPrediction)
            .where(AIPrediction.id_archivo == file_id)
        )

        existing_rows   = list(self.session.scalars(statement).all())
        existing        = {(row.datetime_inicio,row.window_seconds,row.class_name): row for row in existing_rows}

        seen_keys       = set()
        prediction_rows = []

        for result in results:

            key = (result.timestamp,result.window_seconds,result.class_name)
            row = existing.get(key)

            if row is None:

                row = AIPrediction(
                    id_archivo          = file_id,
                    datetime_inicio     = result.timestamp,
                    window_seconds      = result.window_seconds,
                    class_name          = result.class_name,
                    model_name          = model_name
                )

                self.session.add(row)

            row.probability     = result.probability
            row.prediction_rank = result.rank
            row.threshold       = threshold

            prediction_rows.append(row)
            seen_keys.add(key)

        for key,row in existing.items():

            if key not in seen_keys: self.session.delete(row)

        self.session.flush()
        prediction_ids = [row.id_prediccion for row in prediction_rows]

        if prediction_ids: self.session.execute(
            delete(AIPredictionMeasurement)
            .where(AIPredictionMeasurement.id_prediccion.in_(prediction_ids))
        )

        links = []

        for row,result in zip(prediction_rows,results):

            start = result.timestamp
            end = start + datetime.timedelta(seconds=result.window_seconds)

            for measurement in measurements:

                if(measurement.id_archivo != file_id): raise ValueError(f"La medicion no pertenece al archivo: {file_id}")
                if(start<= measurement.datetime < end): links.append(AIPredictionMeasurement(id_prediccion=row.id_prediccion,id_medicion=measurement.id_medicion))



        self.session.add_all(links)
        self.session.flush()

        return (prediction_rows,links)