import os
import unittest
from datetime import datetime, timedelta, timezone

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from dataclasses import replace

from audio_processing.alarms.models import AlarmResult
from audio_processing.persistence.models import (
    AcousticAlarm,
    AcousticAlarmMeasurement,
    AcousticMeasurement,
    Campaign,
    Contexto,
    Device,
    Punto,
    SourceFile,
    SourceFileProcessing,
)
from audio_processing.persistence.repositories import AlarmRepository,FileRepository


class TestAlarmRepository(unittest.TestCase):

    def setUp(self):

        url = os.getenv("AUDIO_PROCESSING_TEST_DATABASE_URL")

        if not url:

            self.skipTest("Define AUDIO_PROCESSING_TEST_DATABASE_URL")

        self.engine = create_engine(url)
        self.connection = self.engine.connect()
        self.outer_transaction = self.connection.begin()

        self.session = Session(
            bind=self.connection,
            join_transaction_mode="create_savepoint",
        )

        device      = Device(nombre="Test", tipo="test")
        campaign    = Campaign(nombre="Test", referencia_interna="test")
        point       = Punto(nombre="Test", municipio="Test")

        self.session.add_all([device, campaign, point])
        self.session.flush()

        context     = Contexto(
            id_dispositivo      = device.id_dispositivo,
            id_campania         = campaign.id_campania,
            id_punto            = point.id_punto,
        )

        self.session.add(context)
        self.session.flush()
        self.context_id = context.id_contexto

        start = datetime(2026, 1, 1, tzinfo=timezone.utc)
        self.measurements = [
            AcousticMeasurement(
                id_contexto         = self.context_id,
                datetime            = start + timedelta(seconds=i),
                aggregation_seconds = 1,
            )
            for i in range(3)
        ]

        self.session.add_all(self.measurements)
        self.session.flush()

    def tearDown(self):
        self.session.close()
        if self.outer_transaction.is_active:
            self.outer_transaction.rollback()
        self.connection.close()
        self.engine.dispose()

    def make_result(self, alarm_type, measurement_ids):

        start = datetime(2026, 1, 1, tzinfo=timezone.utc)

        return AlarmResult(
            alarm_type          = alarm_type,
            start_time          = start,
            end_time            = start + timedelta(hours=1),
            aggregation_seconds = 3600,
            measurement_ids     = tuple(measurement_ids),
            category            = "HIGH",
        )

    def sync(self, results, scope_ids):

        return AlarmRepository(self.session).sync_for_measurements(
            context_id              = self.context_id,
            measurements            = self.measurements,
            results                 = results,
            scope_measurement_ids   = scope_ids,
        )

    def test_sync_is_idempotent_and_keeps_each_alarm_links(self):

        ids = [m.id_medicion for m in self.measurements]

        results = [
            self.make_result("oca", ids[:2]),
            self.make_result("tonal_frequency", ids[1:]),
        ]

        rows1, links1 = self.sync(results, set(ids))
        
        ids_by_type1 = {row.alarm_type: row.id_alarma for row in rows1}
        self.assertEqual(len(links1), 4)

        rows2, links2 = self.sync(results, set(ids))
        ids_by_type2 = {row.alarm_type: row.id_alarma for row in rows2}

        updated_results = [replace(results[0],aggregation_seconds=900,value=91.2,threshold=65.0,category="Ld",details={"test":"updated"},),results[1]]
        rows3,_ = self.sync(updated_results,set(ids))
        oca = next(row for row in rows3 if row.alarm_type=='oca')

        self.assertEqual(oca.id_alarma, ids_by_type1["oca"])
        self.assertEqual(oca.aggregation_seconds, 900)
        self.assertEqual(oca.value, 91.2)
        self.assertEqual(oca.threshold, 65.0)
        self.assertEqual(oca.category, "Ld")
        self.assertEqual(oca.details, {"test": "updated"})

        self.assertEqual(ids_by_type2, ids_by_type1)
        self.assertEqual(len(links2), 4)

        links_by_alarm = {}

        for link in links2:
            links_by_alarm.setdefault(link.id_alarma, set()).add(link.id_medicion)

        self.assertEqual(links_by_alarm[ids_by_type2["oca"]], set(ids[:2]))
        self.assertEqual(
            links_by_alarm[ids_by_type2["tonal_frequency"]],
            set(ids[1:]),
        )

    def test_sync_deletes_stale_alarm_only_inside_scope(self):

        ids = [m.id_medicion for m in self.measurements]
        current = self.make_result("current", [ids[0]])
        stale = self.make_result("stale", [ids[0]])
        outside_scope = self.make_result("outside_scope", [ids[1]])

        self.sync([current, stale, outside_scope], set(ids))
        self.sync([current], {ids[0]})

        rows = self.session.scalars(
            select(AcousticAlarm).where(
                AcousticAlarm.id_contexto == self.context_id
            )
        ).all()

        self.assertEqual(
            {row.alarm_type for row in rows},
            {"current", "outside_scope"},
        )

        outside_row = next(
            row for row in rows if row.alarm_type == "outside_scope"
        )

        outside_links = self.session.scalars(
            select(AcousticAlarmMeasurement).where(
                AcousticAlarmMeasurement.id_alarma == outside_row.id_alarma
            )
        ).all()

        self.assertEqual(
            {link.id_medicion for link in outside_links},
            {ids[1]},
        )

    def test_file_stage_completion_matches_content_hash(self):

        source_file = SourceFile(id_contexto=self.context_id,filename="stage-test.wav")

        self.session.add(source_file)
        self.session.flush()

        repository = FileRepository(self.session)
        
        old_hash = "a" * 64
        new_hash = "b" * 64

        self.assertFalse(repository.is_stage_complete(file_id=source_file.id_archivo,stage="spl",content_hash=old_hash))

        repository.mark_stage_complete(file_id=source_file.id_archivo,stage='spl',content_hash=old_hash)

        self.assertTrue(repository.is_stage_complete(file_id=source_file.id_archivo,stage="spl",content_hash=old_hash))

        repository.mark_stage_complete(file_id=source_file.id_archivo,stage='spl',content_hash=new_hash)

        self.assertFalse(repository.is_stage_complete(file_id=source_file.id_archivo,stage='spl',content_hash=old_hash))

        self.assertTrue(repository.is_stage_complete(file_id=source_file.id_archivo,stage='spl',content_hash=new_hash))

        records = self.session.scalars(select(SourceFileProcessing)
                                       .where(SourceFileProcessing.id_archivo == source_file.id_archivo)).all()
        
        self.assertEqual(len(records),1)
        self.assertTrue(records[0].software_version)
        



if __name__ == "__main__":
    unittest.main()