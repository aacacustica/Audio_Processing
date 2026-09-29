from pathlib import Path
from zoneinfo import ZoneInfo

import soundfile as sf

from audio_processing.campaign.config import load_config
from audio_processing.persistence.database import Database
from audio_processing.persistence.repositories import MeasurementRepository,FileRepository,ContextRepository
    
from audio_processing.spl.leq_processor import run_leq_for_file
from audio_processing.spl.utils_acoustics import read_calibration_constants, timestamp_from_filename
    
def main():

    config = load_config()

    calibration_file = ( config._config_dir / config.spl.calibration_file ) 
        
    calibration_constants = read_calibration_constants( calibration_file )

    audio_file = Path( "/home/martin/Campañas de test/ACLIMA/C1/3-Medidas/P3 - test/AUDIOMOTH/20251204_111321.wav" )

    info = sf.info(audio_file) 

    timestamp = timestamp_from_filename(audio_file)

    if timestamp.tzinfo is None: timestamp = timestamp.replace(tzinfo=ZoneInfo(config.campaign.timezone))

    duration_seconds = ( info.frames / info.samplerate ) 

         
    results = run_leq_for_file(audio_file=audio_file,calibration_constants=calibration_constants,config=config)
        
    print( f"SPL calculado: {len(results)} resultados" )
        
    db = Database.from_config(config)

    with db.session() as session:

        context_repository = ContextRepository( session)
        repository = FileRepository( session ) 
        measurement = MeasurementRepository(session)

        context = context_repository.get_for_source(
            campaign_name   = config.campaign.name,
            point_name      = "P3 - test",
            device_type     = "audiomoth"
        )

        print(
            "Contexto encontrado:",
            context.id_contexto
        )

        source_file = repository.register(
            context_id      = context.id_contexto,
            filename        = audio_file.name,
            datetime_inicio = timestamp,
            duracion_seconds= duration_seconds,
            sample_rate_hz  = info.samplerate
        )

        print(
            "Archivo registrado:",
            source_file.id_archivo,
            source_file.filename,
        )

        measurements = measurement.replace_for_file(
            context_id      = context.id_contexto,
            file_id         = source_file.id_archivo,
            results         = results
        )

        print(
            f"Mediciones insertadas: "
            f"{len(measurements)}"
        )




if __name__ == "__main__":
    main()