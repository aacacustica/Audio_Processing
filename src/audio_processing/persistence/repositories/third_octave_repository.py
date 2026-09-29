from sqlalchemy.orm import Session

from audio_processing.persistence.models import AcousticMeasurement,AcousticThirdOctaveMeasurements
from audio_processing.spl.models import ThirdOctaveResult


BAND_COLUMNS = {
    12.5:       "band_12_5_db",
    16.0:       "band_16_db",
    20.0:       "band_20_db",
    25.0:       "band_25_db",
    31.5:       "band_31_5_db",
    40.0:       "band_40_db",
    50.0:       "band_50_db",
    63.0:       "band_63_db",
    80.0:       "band_80_db",
    100.0:      "band_100_db",
    125.0:      "band_125_db",
    160.0:      "band_160_db",
    200.0:      "band_200_db",
    250.0:      "band_250_db",
    315.0:      "band_315_db",
    400.0:      "band_400_db",
    500.0:      "band_500_db",
    630.0:      "band_630_db",
    800.0:      "band_800_db",
    1000.0:     "band_1000_db",
    1250.0:     "band_1250_db",
    1600.0:     "band_1600_db",
    2000.0:     "band_2000_db",
    2500.0:     "band_2500_db",
    3150.0:     "band_3150_db",
    4000.0:     "band_4000_db",
    5000.0:     "band_5000_db",
    6300.0:     "band_6300_db",
    8000.0:     "band_8000_db",
    10000.0:    "band_10000_db",
    12500.0:    "band_12500_db",
    16000.0:    "band_16000_db",
    20000.0:    "band_20000_db",
}


class ThirdOctaveRepository:

    def __init__(self,session: Session):

        self.session = session

    def add_for_measurements(self,*,measurements: list[AcousticMeasurement],results: list[ThirdOctaveResult]) -> list[AcousticThirdOctaveMeasurements]:

        if len(measurements) != len(results): raise ValueError("Número de mediciones y resultados de tercios diferente:" f"{len(measurements)} != {len(results)}")

        rows = []

        for measurement, result in zip(measurements,results):
           
            if measurement.datetime != result.timestamp: raise ValueError(f"Timestamp SPL/tercios no coincide: {measurement.datetime} != {result.timestamp}")

            values = {column_name: result.bands_db.get(frequency) for frequency,column_name in BAND_COLUMNS.items()}

            row = AcousticThirdOctaveMeasurements(id_medicion = measurement.id_medicion, **values)

            rows.append(row)

        self.session.add_all(rows)
        self.session.flush()

        return rows