from pathlib import Path

from audio_processing.campaign.config import load_config
from audio_processing.persistence.database import Database
from audio_processing.persistence.repositories.measurement_repository import MeasurementRepository
    
from audio_processing.spl.leq_processor import run_leq_for_file
from audio_processing.spl.utils_acoustics import read_calibration_constants
    
def main():

    config = load_config()

    calibration_file = ( config._config_dir / config.spl.calibration_file ) 
        
    calibration_constants = read_calibration_constants( calibration_file )

    audio_file = Path( "/home/martin/Campañas de test/ACLIMA/C1/3-Medidas/P3 - test/AUDIOMOTH/20251204_111321.wav" ) 
         
    results = run_leq_for_file(audio_file=audio_file,calibration_constants=calibration_constants,config=config)
        
    print( f"SPL calculado: {len(results)} resultados" )
        
    db = Database.from_config(config)

    with db.session() as session:

        repository = MeasurementRepository( session ) 
        measurements = repository.replace_for_file(context_id=1,file_id=1,results=results)

        print( f"Mediciones insertadas: {len(measurements)}" ) 




if __name__ == "__main__":
    main()