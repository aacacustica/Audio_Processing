from audio_processing.campaign.config import load_config
from audio_processing.peaks.processor import detect_peaks
from audio_processing.persistence.database import Database
from audio_processing.persistence.repositories import MeasurementRepository


def main():

    config = load_config()

    db = Database.from_config(
        config
    )

    with db.session() as session:

        repository = MeasurementRepository(
            session
        )

        measurements = repository.list_by_file(
            2
        )

        results = detect_peaks(
            measurements,
            window_size=config.peaks.window_size,
            adding_threshold=(
                config.peaks.adding_threshold
            ),
            width=config.peaks.width,
            prominence=config.peaks.prominence,
        )

        print(
            f"Mediciones: {len(measurements)}"
        )

        print(
            f"Picos detectados: {len(results)}"
        )

        for peak in results:

            print()
            print(
                f"Pico:        {peak.peak_timestamp}"
            )
            print(
                f"Inicio:      {peak.start_time}"
            )
            print(
                f"Fin:         {peak.end_time}"
            )
            print(
                f"Duración:    {peak.duration_seconds} s"
            )
            print(
                f"Muestras:    {peak.sample_count}"
            )
            print(
                f"LA pico:     {peak.peak_la_db:.2f} dB"
            )
            print(
                f"Leq evento:  {peak.leq_db:.1f} dB"
            )
            print(
                f"Prominencia: {peak.prominence_db:.2f} dB"
            )
            print(
                f"LA values:   {peak.la_values}"
            )


if __name__ == "__main__":
    main()