from datetime import datetime, timezone

from audio_processing.campaign.config import load_config
from audio_processing.persistence.database import Database
from audio_processing.persistence.repositories.measurement_repository import (
    MeasurementRepository,
)


def main():

    config = load_config()
    db = Database.from_config(config)

    with db.session() as session:

        repo = MeasurementRepository(session)

        measurement = repo.add(
            file_id =1,
            timestamp=datetime.now(timezone.utc),
            aggregation_seconds=1.0,
            la_db=63.2,
            lc_db=68.4,
            lz_db=70.1,
            la_max_db=67.8,
            la_min_db=58.4,
            lc_la_db=5.2,
        )

        print(
            "Medición creada:",
            measurement.id_medicion,
        )


if __name__ == "__main__":
    main()