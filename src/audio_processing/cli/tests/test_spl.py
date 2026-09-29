from pathlib import Path

import numpy as np

from audio_processing.campaign.config import load_config
from audio_processing.spl.leq_processor import run_leq_for_file,run_third_octave_for_file
from audio_processing.spl.utils_acoustics import read_calibration_constants

def main():

    config = load_config()

    calibration_file = config._config_dir / config.spl.calibration_file 
    calibration_constants = read_calibration_constants( calibration_file ) 
    audio_file = Path("/home/martin/Campañas de test/ACLIMA/C1/3-Medidas/P3 - test/AUDIOMOTH/20251204_111321.wav")
    
    results = run_leq_for_file( 
        audio_file              = audio_file,
        calibration_constants   = calibration_constants,
        config                  = config, )

    print( "Resultados acústicos:", len(results) )

    for result in results[:5]:
        print(result)

    third_results = run_third_octave_for_file(
        audio_file              = audio_file,
        calibration_constants   = calibration_constants,
        config                  = config
    )

    print("Resultados tercios:",len(third_results))

    print("Bandas del primer segundo:",len(third_results[0].bands_db))

    print(third_results[0])

    third_octave_total = 10 * np.log10(sum(10**(level_db / 10) for level_db in third_results[0].bands_db.values()))

    print("Suma energética tercios:",round(third_octave_total,2),"dB")
    print("LZ:",results[0].lz_db,"dB")

if __name__ == "__main__":
    main()