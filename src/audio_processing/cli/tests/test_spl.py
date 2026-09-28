from pathlib import Path

from audio_processing.campaign.config import load_config
from audio_processing.spl.leq_processor import run_leq_for_file
from audio_processing.spl.utils_acoustics import read_calibration_constants

def main():

    config = load_config()

    calibration_file = ( config._config_dir / config.spl.calibration_file ) 
    calibration_constants = ( read_calibration_constants( calibration_file ) ) 
    audio_file = Path( "/home/martin/Campañas de test/ACLIMA/C1/3-Medidas/P3 - test/AUDIOMOTH/20251204_111321.wav" )
    results = run_leq_for_file( audio_file=audio_file, calibration_constants=calibration_constants, config=config, )

    print( "Resultados:", len(results) )

    for result in results[:5]:
        print(result)


if __name__ == "__main__":
    main()