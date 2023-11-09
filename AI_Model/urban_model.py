import json
import numpy as np
import soundfile as sf
from scipy.signal import medfilt
import os
from tqdm import tqdm
import datetime
import pandas as pd
import re
import logging
import argparse
import params
import yamnet as yamnet_model
import tensorflow as tf
tf.get_logger().setLevel(logging.ERROR)

def audios_long(audio_files):
    """Print how long the audio files are."""
    for file in audio_files:
        try:
            wav_data, sr = sf.read(os.path.join(audio_path, file), dtype=np.int16)
            if (len(wav_data) / sr) < 60:
                print("The audio is {:.2f} seconds long".format(len(wav_data) / sr))
            elif (len(wav_data) / sr / 60) > 1 and (len(wav_data) / sr / 60) < 60:
                print("The audio is {:.2f} minutes long".format(len(wav_data) / sr / 60))
            else:
                print("The audio is {:.2f} hours long".format(len(wav_data) / sr / 3600))
        except Exception as e:
                print(e)
        
def print_audio_time(w_size:int, sr:int, wav_data:list):
    """Prints the audio time."""
    # Audio time length
    if (len(wav_data) / sr) < 60:
        print("\nThe audio is {:.2f} seconds long".format(len(wav_data) / sr))
    elif (len(wav_data) / sr / 60) > 1 and (len(wav_data) / sr / 60) < 60:
        print("\nThe audio is {:.2f} minutes long".format(len(wav_data) / sr / 60))
    else:
        print("\nThe audio is {:.2f} hours long".format(len(wav_data) / sr / 3600))
    
    # Analysis window size
    if w_size / sr < 60:
        print("Analysis window size: {} seconds\n".format(w_size / sr))
    else:
        print("Analysis window size: {} minutes\n".format(w_size / sr / 60))

def get_predictions(audio_files:list, fs_model:float, w_time:int, taxonomy_mapping:dict, n_predictions:int):
    """Get predictions from yamnet model in a collection of audio files averaged over an analysis window and map to custom classes."""
    params.PATCH_HOP_SECONDS = 1 # 1 Hz frame rate.
    params.SAMPLE_RATE = int(fs_model) # Sampling frequency.
    print(f"\nModel configured with fs= {int(fs_model)}")
    
    yamnet = yamnet_model.yamnet_frames_model(params)
    yamnet.load_weights('yamnet.h5')
    class_names = yamnet_model.class_names('yamnet_class_map.csv')

    audio_classes = []
    audio_classes_original = [] 
    probs = []
    probs_original = [] 
    datetimes = []
    files = []

    # for file in tqdm(audio_files[:n_predictions]):
    for file in tqdm(audio_files):
        print(f"\n\nProcessing audio file  -->  {file}")
        wav_data, sr = sf.read(os.path.join(audio_path, file), dtype=np.int16)
        waveform = wav_data / 32768.0  # 2**15
        w_size = int(w_time * 60 * sr)
        # w_size = w_time * 60 * sr
        print_audio_time(w_size, sr, wav_data)      

        count = 0
        if len(waveform) > w_size:
            for fstart in range(0, len(waveform) - w_size + 1, w_size):
                scores, _ = yamnet.predict(np.reshape(waveform[fstart:fstart+w_size], [1, -1]), steps=1)
                prediction = np.mean(scores, axis=0)

                # top_original = np.argsort(prediction)[::-1][:5]
                top_original = np.argsort(prediction)[::-1][:n_predictions]
                clip_classes_original = [class_names[i] for i in top_original]
                prob_classes_original = [prediction[i] for i in top_original]
                audio_classes_original.append(clip_classes_original)
                probs_original.append(prob_classes_original)

                # adjust scores based on the new taxonomy
                new_scores = {key: 0 for key in set(taxonomy_mapping.values())}
                for original_class, mapped_class in taxonomy_mapping.items():
                    index = np.where(class_names == original_class)[0][0]
                    new_scores[mapped_class] += prediction[index]
    
                total_score = sum(new_scores.values())
                for key in new_scores:
                    new_scores[key] /= total_score
                
                top_i = np.argsort(list(new_scores.values()))[::-1][:n_predictions]

                date = datetime.datetime.strptime(file.split('.')[0], '%Y%m%d_%H%M%S')
                date = date + datetime.timedelta(minutes=w_time * count)
                datetimes.append(date)

                clip_classes = []
                prob_classes = []

                for i in top_i:
                    clip_classes.append(list(new_scores.keys())[i])
                    prob_classes.append(list(new_scores.values())[i])
                audio_classes.append(clip_classes)
                probs.append(prob_classes)
                files.append(file)
                
                if len(clip_classes) == 1:
                    print(f"\nWe are adding 1 class for window analysis.\n")
                else:
                    print(f"\nWe are adding {len(clip_classes)} classes for window analysis.\n")
                
        else:
            print("Audio shorter than analysis window")

    data_dict = {'files': files, 
                 'datetime': datetimes, 
                 'classes_custom': audio_classes, 
                 'probabilities_custom': probs,
                 'sum_probs_custom': [sum(x) for x in probs],
                 'classes_original': audio_classes_original, 
                 'probabilities_original': probs_original,
                 'sum_probs_original': [sum(x) for x in probs_original]} 

    # sort by datetime in ascending order
    df = pd.DataFrame(data_dict)
    df_sorted = df.sort_values(by='datetime')
    
    return df_sorted

def argument_parser():
    parser = argparse.ArgumentParser(description='Inferencia Yamnet de todos los archivos de audio en un directorio')
    parser.add_argument('-p','--path', type=str, help='Directorio para ser procesado')
    parser.add_argument('-a', '--abrev', type=str, help='Abreviación para identificar las predicciones generadas')
    parser.add_argument('-w','--window', type=float, default=1, help='tamaño ventana de analisis en minutos')
    parser.add_argument('-n','--n-predictions', type=int, default=1, help='Number of predictions to be generated')
    parser.add_argument('-r', '--result-folder', type=str, default=None, help='Location where the results should be saved')
    args = parser.parse_args()
    return args

if __name__ == "__main__":
    args = argument_parser()

    if not args.n_predictions:
        n_predictions = 5
    else:
        n_predictions = args.n_predictions

    if not args.path:
        audio_path = 'E:/AUDIOS_ID/NOISEPORT_audios_portbilbao/oficinas_portlab-20221028/reduced_audios/20221025'
    else:
        audio_path = args.path
    
    # variables 
    if not args.abrev:
        abrev = os.path.basename(audio_path) 
        print(f"\nAbreviación para identificar las predicciones generadas: {abrev}")
    else:
        abrev = args.abrev

    # set window size in minutes
    analysis_window_time = args.window # ventana de analisis en minutos
    extract_audio = False # bandera para extraer clips de audio

    # get audio files
    audio_files = []
    for file in os.listdir(audio_path):
        if (file.endswith('.WAV') or file.endswith('.wav')):
            audio_files.append(file)
        else:
            print(f"Archivo {file} no es un archivo de audio")
    print(f"\n{len(audio_files)} archivos de audio encontrados")
    # audio_files = [file for file in os.listdir(audio_path) if (file.endswith('.WAV') or file.endswith('.wav'))]
    # audios_long(audio_files)
    # exit()
    # get sample rate of the collection
    sample_rates = []
    valid_audio_files = []
    for file in audio_files:
        try:
            metadata = sf.info(os.path.join(audio_path,file))
            sample_rates.append(metadata.samplerate)
            valid_audio_files.append(file)
        except Exception as e:
            print(e)
            print('Error en el archivo {}'.format(file))

    sample_rates = np.array(sample_rates)

    if np.std(sample_rates) < 0.1:
        fs_model = np.median(sample_rates)
        print('\nTodos los audios tienen una frecuencia de muestreo de  {} Hz'.format(np.median(sample_rates)))
    else:
        fs_model = np.median(sample_rates)
        print('\nLos audios tienen una frecuencia de muestreo diferente, El modelo evaluara la frecuencia predominante {}'.format(fs_model))

    if args.result_folder:
        results_folder = args.result_folder
    else:
        for subdir in audio_path.split('\\'):
            if re.search(r'\d', subdir) != None:
                results_folder = subdir

    if not(os.path.isdir(results_folder)):
        os.mkdir(results_folder)
        print(f"\nCarpeta de resultados {results_folder} creada")

    # allow growth 
    physical_devices = tf.config.experimental.list_physical_devices('GPU')

    for device in physical_devices:
        tf.config.experimental.set_memory_growth(device, True)

    with open('taxonomy_mapping.json', 'r') as f:
        taxonomy_mapping = json.load(f)

    data_df = get_predictions(audio_files=valid_audio_files,
                          fs_model=fs_model,
                          w_time=analysis_window_time,
                          taxonomy_mapping=taxonomy_mapping,
                          n_predictions=n_predictions)

    print(f"{len(valid_audio_files)} procesados")

    # csv File
    predictions_file = f'Urban_Model_{abrev}_{n_predictions}.csv'
    data_df.to_csv(os.path.join(results_folder,predictions_file), index=False)
    print(f"Archivo de prediciones creado en {os.path.abspath(os.path.join(results_folder,predictions_file))}")

