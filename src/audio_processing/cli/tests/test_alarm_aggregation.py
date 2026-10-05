from audio_processing.alarms.aggregation import (
    aggregate_measurements,
)
from audio_processing.campaign.config import (
    load_config,
)
from audio_processing.persistence.database import (
    Database,
)
from audio_processing.persistence.repositories import (
    MeasurementRepository,
    ThirdOctaveRepository,
    PeakRepository,
)

from audio_processing.alarms.processor import detect_lmax_alarms,detect_l90_dynamic_alarms,detect_lc_la_alarms,detect_oca_alarms


config = load_config(
    "configs/campaign.example.yaml",
    profile_name="hourly",
)

db = Database.from_config(config)

FILE_ID = 2
CONTEXT_ID = 1


with db.session() as session:

    measurement_repository = (
        MeasurementRepository(session)
    )

    third_octave_repository = (
        ThirdOctaveRepository(session)
    )

    peak_repository = (
        PeakRepository(session)
    )

    measurements = (
        measurement_repository
        .list_by_file(FILE_ID)
    )

    measurement_ids = [
        measurement.id_medicion
        for measurement in measurements
    ]

    print(
    "Rango de mediciones:",
    min(measurement_ids),
    max(measurement_ids),
    )

    print(
        "¿765 está en measurement_ids?:",
        765 in measurement_ids,
    )

    print(
        "Primeros IDs:",
        measurement_ids[:5],
    )

    print(
        "Últimos IDs:",
        measurement_ids[-5:],
    )

    third_octaves = (
        third_octave_repository
        .list_by_measurements(
            measurement_ids
        )
    )

    peak_apex_ids = (
        peak_repository
        .list_apex_measurement_ids(
            context_id=CONTEXT_ID,
            measurement_ids=measurement_ids,
        )
    )

    aggregations = aggregate_measurements(
        measurements,
        third_octaves=third_octaves,
        peak_apex_measurement_ids=(
            peak_apex_ids
        ),
        aggregation_seconds=(
            config.alarms
            .aggregation_seconds
        ),
        timezone=(
            config.campaign.timezone
        ),
    )


print(
    "Mediciones:",
    len(measurements),
)

print(
    "Tercios:",
    len(third_octaves),
)

print(
    "Ápices de pico:",
    peak_apex_ids,
)

print(
    "Agregados:",
    len(aggregations),
)


for aggregation in aggregations:

    print()
    print(
        "Inicio:",
        aggregation.start_time,
    )
    print(
        "Fin:",
        aggregation.end_time,
    )
    print(
        "Mediciones:",
        len(
            aggregation.measurement_ids
        ),
    )
    print(
        "LA:",
        aggregation.la_db,
    )
    print(
        "LC:",
        aggregation.lc_db,
    )
    print(
        "LZ:",
        aggregation.lz_db,
    )
    print(
        "LAmax:",
        aggregation.la_max_db,
    )
    print(
        "LAmin:",
        aggregation.la_min_db,
    )
    print(
        "P90:",
        aggregation.percentile_90_db,
    )
    print(
        "LC-LA mean:",
        aggregation.lc_la_mean_db,
    )
    print(
        "N picos:",
        aggregation.n_peaks,
    )
    print(
        "N tercios:",
        len(
            aggregation.third_octaves_db
        ),
    )

lmax_alarms = detect_lmax_alarms(aggregations,threshold_db=95)
l90_alarms = detect_l90_dynamic_alarms(aggregations,threshold_db=5,rolling_window=3)
oca_alarms = detect_oca_alarms(aggregations,oca_type='OCA_RESIDENTIAL')
lc_la_alarms = detect_lc_la_alarms(aggregations,normative_threshold_db=10,dynamic_threshold_db=3)

print()
print(
    "Alarmas OCA:",
    len(oca_alarms),
)

print(
    "Alarmas Lmax:",
    len(lmax_alarms),
)

print(
    "Alarmas LC-LA:",
    len(lc_la_alarms),
)

print(
    "Alarmas L90:",
    len(l90_alarms),
)

for alarm in oca_alarms:
    print(
        "OCA:",
        alarm.value,
        ">",
        alarm.threshold,
        alarm.category,
    )