from __future__ import annotations
from sqlalchemy import and_,delete,or_,select
from sqlalchemy.orm import Session

from audio_processing.alarms.models import AlarmResult
from audio_processing.persistence.models import AcousticAlarm,AcousticAlarmMeasurement,AcousticMeasurement

class AlarmRepository:

    def __init__(self,session: Session):
        self.session = session

    def sync_for_measurements(self,*,context_id: int, measurements: list[AcousticMeasurement],results: list[AlarmResult],scope_measurement_ids: set[int] | None = None) -> tuple[list[AcousticAlarm],list[AcousticAlarmMeasurement]]:

        if not measurements: return [],[]

        measurement_by_id = {measurement.id_medicion: measurement for measurement in measurements}

        measurement_ids = set(measurement_by_id)

        for measurement in measurements:

            if measurement.id_contexto != context_id: raise ValueError(f" Hay mediciones que no pertenecen al contexto {context_id}")

        if scope_measurement_ids is None: scope_measurement_ids = measurement_ids.copy()
        else: scope_measurement_ids = set(scope_measurement_ids)

        unknown_scope_ids = scope_measurement_ids - measurement_ids

        if unknown_scope_ids: raise ValueError(f"El scope contiene mediciones no incluidas en measurements: {sorted(unknown_scope_ids)}")

        # -------------------------------------------------
        # VALIDAR RESULTADOS
        # -------------------------------------------------

        result_keys = set()

        for result in results:

            key = (result.alarm_type,result.start_time,result.end_time)

            if key in result_keys: raise ValueError(f"Resultado de la alarma duplicado: {key}")

            result_keys.add(key)

            result_measurement_ids = set(result.measurement_ids)
            unknown_ids = result_measurement_ids - measurement_ids

            if unknown_ids: raise ValueError(f"La alarma contiene mediciones que no están disponibles: {sorted(unknown_ids)}")

        
        # -------------------------------------------------
        # ALARMAS EXISTENTES QUE COINCIDEN CON RESULTS
        #
        # Esto es importante aunque sus bridges actuales
        # no intersecten con scope_measurement_ids.
        # -------------------------------------------------

        existing_by_key = {}

        if results: 
            conditions = [and_(AcousticAlarm.alarm_type == result.alarm_type,
                                       AcousticAlarm.start_time == result.start_time,
                                       AcousticAlarm.end_time == result.end_time) for result in results]
            statement = (select(AcousticAlarm)
                         .where(AcousticAlarm.id_contexto == context_id,
                                or_(*conditions),))
            existing_rows = list(self.session.scalars(statement).all())
            existing_by_key = {
                (row.alarm_type,
                row.start_time,
                row.end_time,):row for row in existing_rows
            }
        # -------------------------------------------------
        # ALARMAS EXISTENTES DENTRO DEL SCOPE
        #
        # Solo estas pueden considerarse stale.
        # -------------------------------------------------

        stale_candidates = []

        if scope_measurement_ids:

            statement = (select(AcousticAlarm)
                         .join(AcousticAlarmMeasurement,
                               AcousticAlarmMeasurement.id_alarma == AcousticAlarm.id_alarma)
                        .where(AcousticAlarm.id_contexto == context_id, AcousticAlarmMeasurement.id_medicion.in_(scope_measurement_ids)).distinct())

            stale_candidates = list(self.session.scalars(statement).all())

  
        # -------------------------------------------------
        # INSERT / UPDATE
        # -------------------------------------------------

        alarm_rows = []
        seen_keys = set()

        for result in results:

            key = (
                result.alarm_type,
                result.start_time,
                result.end_time,
            )          

            row = existing_by_key.get(key)

            if row is None:

                row = AcousticAlarm(
                    id_contexto=context_id,
                    alarm_type=result.alarm_type,
                    start_time=result.start_time,
                    end_time=result.end_time
                )

                self.session.add(row)

            row.aggregation_seconds = (result.aggregation_seconds)
            row.value = result.value
            row.threshold = result.threshold
            row.category = result.category
            row.details = result.details
            alarm_rows.append(row)
            seen_keys.add(key)

        self.session.flush()

        # -------------------------------------------------
        # BORRAR ALARMAS OBSOLETAS SOLO EN ESTE SCOPE
        # -------------------------------------------------


        for row in stale_candidates:

            key = (
                row.alarm_type,
                row.start_time,
                row.end_time
            )

            if key not in seen_keys: self.session.delete(row)
        
        self.session.flush()

        # -------------------------------------------------
        # RECONSTRUIR BRIDGES DE ALARMAS ACTUALES
        # -------------------------------------------------

        alarm_ids = [row.id_alarma for row in alarm_rows]

        if alarm_ids:
            self.session.execute(
                delete(AcousticAlarmMeasurement)
                .where(AcousticAlarmMeasurement.id_alarma.in_(alarm_ids))
            )        

        links = []

        for row,result in zip(alarm_rows,results):

            result_measurement_ids = (dict.fromkeys(result_measurement_ids))

            for measurement_id in result_measurement_ids:

                links.append(AcousticAlarmMeasurement(
                    id_alarma = row.id_alarma,
                    id_medicion = measurement_id
                ))

        self.session.add_all(links)
        self.session.flush()

        return alarm_rows,links