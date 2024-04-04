import pandas as pd
import soundfile as sf
from scipy.signal import lfilter
import numpy as np
from pyfilterbank.splweighting import a_weighting_coeffs_design
from pyfilterbank.splweighting import c_weighting_coeffs_design
from utils import *
import argparse
import os
import re
import audio_metadata

from tqdm import tqdm
import logging
import datetime

######################
## Function Section ##
######################
def leq_levels_oct(audio_files:list ,fs_filterbanks:float , w_size: int, C:float, results_folder:str):
    """ Write a CSV with noise levels and 1/3 octave spectrum of a list of audio files

    Args:
        audio_files (list): List of audio files
        fs_filterbanks (float): Common sample rate of the audios to design the filters
        w_size (int): Analysis Window size in number of samples, default set to fs.
        C (float): Calibration constant for the audio recorder device.
    """

    # ponderaciones A y C
    bA, aA = a_weighting_coeffs_design(fs_filterbanks)
    bC, aC = c_weighting_coeffs_design(fs_filterbanks)
    # filterbanks
    freqs, foo = frequencies_fractional_octaves(-19, 13, 1000, 3)
    third_oct, octave = filterbanks(fs_filterbanks)
    logger.info(f'Filtros de octava y ponderaciones creados con fs {fs_filterbanks}')

    
    col_names = ['LA','LC','LZ','LAmax','LAmin']
    w_fast_samples = int(w_size / 8) 
    band_names = [str(np.round(band,2)) for band in freqs]
    col_names.extend(band_names)
    df_all = pd.DataFrame()
    
    n_audio_files = 1
    # for audio_file in tqdm(audio_files[:n_audio_files]):      
    for audio_file in tqdm(audio_files):
        try:        
            db = []
            x, _ = sf.read(os.path.join(audio_path,audio_file))
            
            # aplicar ponderacion a y c a la señal
            y_A_weighted = lfilter(bA, aA, x)
            y_C_weighted = lfilter(bC, aC, x)

            for fstart in range(0, len(x) - w_size + 1, w_size):
                frame = x[fstart:fstart + w_size]
                yA = y_A_weighted[fstart:fstart + w_size]
                yC = y_C_weighted[fstart:fstart + w_size]

                # niveles totales con ponderaciones
                LA = get_db_level(yA, C)
                LC = get_db_level(yC, C)
                LZ = get_db_level(frame, C)

                fast_levels = []
                for idx_start in range(0, len(frame) - w_fast_samples + 1, w_fast_samples):
                    subframe = frame[idx_start:idx_start+w_fast_samples]
                    LAf = get_db_level(yA, C)
                    fast_levels.append(LAf)
                
                Lmax = np.max(fast_levels)
                Lmin = np.min(fast_levels)
                
                # niveles tercio de octava en ponderacion Z
                oct_level_temp = get_oct_levels(frame, third_oct,C)
                
                # creacion listas temporales
                level_temp =  [LA,LC,LZ,Lmax, Lmin]
                level_temp.extend(oct_level_temp)
                db.append(level_temp)
            
            if len(db) > 0:
                # round
                db = np.array(db)
                db = np.round(db,2)
                # write file
                name = audio_file.split(".")[0]
                df_history = pd.DataFrame(db,columns=col_names)
                df_history['filename'] = audio_file
                start = datetime.datetime.strptime(name, '%Y%m%d_%H%M%S')
                n = len(df_history)
                df_history['date'] = pd.date_range(start=start, freq='s', periods=n)
                df_all = pd.concat([df_all,df_history])
            else:
                logger.error(f"No data to write for file {audio_file}")
        
        except Exception as e:
            logger.error(f"Error processing file {audio_file}: {e}", exc_info=True)
            continue            

    # check date column is in ascending order
    if not df_all['date'].is_monotonic_increasing:
        # If not, sort it by the 'date' column
        df_all = df_all.sort_values('date')
   
    file_ext = "_spl_oct.csv"
    results_folder = results_folder.rstrip('\\').rstrip('"')  
 
    if "192.168.205.117" in results_folder:
        folder_name = results_folder.replace(" ", "_").split("\\")[6] + file_ext
        print(f"\nFolder name: {folder_name}")
    else:
        folder_name = results_folder.split("\\")[-1] + file_ext
        print(folder_name)
 
    file_name_csv = os.path.join(results_folder, folder_name)
    print(f"\nFile name csv: {file_name_csv}")
   
    df_all.to_csv(file_name_csv)
 
    logger.info(f'{len(audio_files)} Archivos procesados con éxito')
    logger.info(f'Archivo {file_name_csv} creado con éxito')

######################
## Processing Section ##
######################

if __name__ == '__main__':
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    file_hander = logging.FileHandler('spl_level_logs.log')
    formatter =logging.Formatter('%(asctime)s:%(levelname)s:%(name)s:%(message)s')
    file_hander.setFormatter(formatter)
    logger.addHandler(file_hander)

    parser = argparse.ArgumentParser(description='Calculo de niveles los archivos de audio en un directorio')
    parser.add_argument('-p','--path', type=str, help='Directorio para ser procesado')
    parser.add_argument('-a', '--abrev', type=str, help='Abreviación para identificar las predicciones generadas')
    parser.add_argument('-r','--results-path', type=str, help='Directorio para guardar los resultados')

    args = parser.parse_args()
    if not args.path:
        audio_path = "\\192.168.205.117\AAC_Server\OCIO\MER_OCIO_BILBAO_2023\BASURTO\AUDIOMOTH"
    else:
        audio_path = args.path
    
    #results directory
    if args.results_path:
        results_dir = args.results_path
    else:
        parent_dir = os.path.dirname(audio_path)
        results_folder = "Results"  
        results_dir = os.path.join(parent_dir, results_folder)
        if not os.path.isdir(results_dir):
            os.mkdir(results_dir)
            print(f"Carpeta de resultados 'Results' creada en {os.path.abspath(results_dir)}")
    
    if not args.abrev:
        abrev = os.path.basename(audio_path) # Nombre para ser usado en carpeta de resultados
    else:
        abrev = args.abrev

    # Data Integrity
    assert os.path.exists(audio_path) , f"Directorio no existe {audio_path}"
    logger.info(f'Directorio Valido: {audio_path}')
    audio_files = [file for file in os.listdir(audio_path) if (file.endswith('.WAV') or file.endswith('.wav'))]
    assert len(audio_files) >= 1, f'Directorio no contiene audios {audio_path}'
    logger.info(f'Directorio contiene {len(audio_files)} audios')

    # get sample rate of the collection
    sample_rates = []
    valid_audio_files = []
    for file in audio_files:
        try:
            metadata = sf.info(os.path.join(audio_path,file))
            sample_rates.append(metadata.samplerate)
            valid_audio_files.append(file)
        except Exception as e:
            logger.info('',exc_info=True)
    sample_rates = np.array(sample_rates)
    logger.info(f'Directorio contiene {len(valid_audio_files)} audios validos')
    if np.std(sample_rates) < 0.1:
        fs_filterbanks = np.median(sample_rates)
        logger.info('Todos los audios tienen una frecuencia de muestreo de  {} Hz'.format(fs_filterbanks))
    else:
        fs_filterbanks = np.median(sample_rates)
        logger.info('los audios tienen una frecuencia de muestreo diferente, El modelo evaluara la frecuencia predominante {}'.format(fs_filterbanks))

    # Get calibration constant
    metadata = audio_metadata.load(os.path.join(audio_path, valid_audio_files[0]))
    calibration_dict = {
        "24F3190361CBDDE4": -13.91,
        "249BC30461CBDE81": -13.31,
        "24E144025F5777C9": -13.5,
        "24F3190160370890": -14.29,
        "243B1F0663FA5A51": -13.43,
        "2453AC0263FAA205": -12.32,
        "2474750763FAA212": -12.06,
        "2453AC0263FA59F5": -13.51,
        "243B1F0663FA5A6C": -14.01,
        "24F3190863FAA254": 0,
        "2453AC0263FA5AAD": -14.08,
        "24E1440163FAA22D": -12.25,
        "2474750763FBD3A7": -12.81,
        "24F3190863FAA27B": -12.47
    } # LA PALMA(ARMAS)

    if "artist" in list(metadata["tags"].keys()):
        device_id = metadata["tags"]["artist"][0].split(" ")[1]
        C = calibration_dict[device_id]  
        logger.info(f"Calibration constant set to {C} for {device_id}")  
    else:
        C = -10.16
        logger.info(f"Calibration constant set to {C} for songmeter")

    w_size = int(fs_filterbanks) 

    leq_levels_oct(audio_files=valid_audio_files,
                             fs_filterbanks=fs_filterbanks,
                             w_size=w_size,
                             C=C,
                             results_folder=results_dir)
    
    
    print(f"Resultados guardados en {os.path.abspath(results_dir)}")