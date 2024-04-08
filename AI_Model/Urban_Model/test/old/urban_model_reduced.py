
import numpy as np
import soundfile as sf
import os
from tqdm import tqdm
import datetime
import pandas as pd
import argparse

import params
import yamnet as yamnet_model
import tensorflow as tf
import subprocess

import logging

tf.get_logger().setLevel(logging.ERROR)

logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s', 
                    filename='urban_model_reduced.log',
                    )

def list_git_tags():
    try:
        tags = tags = subprocess.check_output(["git", "tag"]).strip().decode()
        return tags.split('\n')
    except subprocess.CalledProcessError:
        return None
    
def get_stable_version():
    tags = list_git_tags()
    tag_selected = tags[-1]
    tag_selected = tag_selected.replace(".", "_")
    
    return tag_selected

def audios_long(audio_files):
    for file in audio_files:
        try:
            wav_data, sr = sf.read(os.path.join(audio_path, file), dtype=np.int16)
            if (len(wav_data) / sr) < 60:
                logging.info("The audio is {:.2f} seconds long".format(len(wav_data) / sr))
            elif (len(wav_data) / sr / 60) > 1 and (len(wav_data) / sr / 60) < 60:
                logging.info("The audio is {:.2f} minutes long".format(len(wav_data) / sr / 60))
            else:
                logging.info("The audio is {:.2f} hours long".format(len(wav_data) / sr / 3600))
        except Exception as e:
                logging.error(e)

def print_audio_time(w_size:int, sr:int, wav_data:list):
    if (len(wav_data) / sr) < 60:
        logging.info("The audio is {:.2f} seconds long".format(len(wav_data) / sr))
    elif (len(wav_data) / sr / 60) > 1 and (len(wav_data) / sr / 60) < 60:
        logging.info("The audio is {:.2f} minutes long".format(len(wav_data) / sr / 60))
    else:
        logging.info("The audio is {:.2f} hours long".format(len(wav_data) / sr / 3600))
    
    # Analysis window size
    if w_size / sr < 60:
        logging.info("Analysis window size: {} seconds".format(w_size / sr))
    else:
        logging.info("Analysis window size: {} minutes".format(w_size / sr / 60))

def get_predictions(audio_files:list, fs_model:float, w_time:int, n_predictions:int):
    params.PATCH_HOP_SECONDS = 1 # 1 Hz frame rate.
    params.SAMPLE_RATE = int(fs_model) # Sampling frequency.
    logging.info(f"Model configured with fs= {int(fs_model)}")
    
    yamnet = yamnet_model.yamnet_frames_model(params)
    yamnet.load_weights('yamnet.h5')
    class_names = yamnet_model.class_names('yamnet_class_map.csv')

    classes_original = [] 
    probs_original = [] 
    datetimes = []
    files = []
    spectrograms = []

    for file in tqdm(audio_files):
        logging.info(f"Processing audio file  -->  {file}")
        try:
            wav_data, sr = sf.read(os.path.join(audio_path, file), dtype=np.int16)
        except Exception as e:
            logging.error(f"Failed to read file {file}: {e}")
            continue
        
        waveform = wav_data / 32768.0  # 2**15
        w_size = int(w_time * sr) # w_size = int(w_time * 60 * sr)
        print_audio_time(w_size, sr, wav_data)

        if len(waveform) > w_size:
            for count, fstart in enumerate(range(0, len(waveform) - w_size + 1, w_size)):
                scores, spectrogram = yamnet(np.reshape(waveform[fstart : fstart + w_size], [1, -1]), steps=1)

                # prediction, scores
                prediction = np.mean(scores, axis=0)
                spectrogram = spectrogram.numpy()
                logging.info(f"Raw predictions ({len(prediction)}) for {file}")
                spectrograms.append(spectrogram)

                top_original = np.argsort(prediction)[::-1][:n_predictions]

                # get the classes and probabilities 
                clip_classes_original = [class_names[i] for i in top_original]
                prob_classes_original = [prediction[i] for i in top_original]

                # append to the lists
                classes_original.append(clip_classes_original)
                probs_original.append(prob_classes_original)

                files.append(file)
                
                date = datetime.datetime.strptime(file.split('.')[0], '%Y%m%d_%H%M%S')
                date = date + datetime.timedelta(minutes=w_time * count)
                datetimes.append(date)

                logging.info(f"Original classes for {file}: {clip_classes_original}")
                logging.info(f"Original probabilities for {file}: {prob_classes_original}")
                
        else:
            logging.warning("Audio shorter than analysis window")

    data_dict = {'file': files, 
                 'datetime': datetimes, 
                 'classes_original': classes_original, 
                 'probabilities_original': probs_original,
                 } 

    df = pd.DataFrame(data_dict)
    df_sorted = df.sort_values(by='datetime')
    return df_sorted

def argument_parser():
    parser = argparse.ArgumentParser(description='Inferencia Yamnet de todos los archivos de audio en un directorio')
    parser.add_argument('-p', '--path', required=True, type=str, help='Path to the audio files')
    parser.add_argument('-a', '--abrev', type=str, help='Name to identify the predictions file')
    parser.add_argument('-w', '--window', type=float, default=899, help='Analysis window size in seconds')
    parser.add_argument('-n', '--n-predictions', type=int, default=3, help='Number of predictions to be generated')
    parser.add_argument('-r', '--result-folder', type=str, default=None, help='Location where the results should be saved')
    args = parser.parse_args()
    return args

if __name__ == "__main__":
    """
    python urban_model.py -p /home/usuario/audios -a "audios_1" -w 14.99 -n 3 -r /home/usuario/resultados
    """
    args = argument_parser()
    # set the version tag
    version_tag = get_stable_version()
    logging.info(f"Version tag: {version_tag}")

    # set path to audio files
    audio_path = args.path
    # check if the path exists
    if not os.path.exists(audio_path):
        raise Exception(f"Path {audio_path} does not exist.")
    
    # set abreviation
    if args.abrev:
        abrev = args.abrev
    else:
        # if the folder contains wavs files: the abrev is the name of that folder
        if os.path.basename(audio_path).endswith('.wav') or os.path.basename(audio_path).endswith('.WAV'):
            abrev = os.path.basename(audio_path).split('.')[0]
            logging.info(f"Location: {abrev}")
        # if else, the abrev is the name of the parent folder
        else:
            abrev = os.path.basename(os.path.dirname(audio_path))
            logging.info(f"Location: {abrev}")
    
    # set analysis window size in minutes
    analysis_window_time = args.window # ventana de analisis en minutos
    # set number of predictions
    n_predictions = args.n_predictions
    # set results folder
    if args.result_folder:
        results_dir = args.result_folder
        if not os.path.exists(results_dir):
            os.makedirs(results_dir)
        make_predicciones = results_dir
    
    else:
        results_dir_name = "5-Resultados"
        resultados_pred = "URBAN_Model"
        
        predictions_folder = "Predictions"
        visualizations_folder = "Visualizations"
        
        resultados_dir = audio_path.split("\\")[2:-3]
        # convert resultados_dir to a os.PathLike object
        resultados_folder_path = os.path.join('\\', *resultados_dir, results_dir_name)        
        if not os.path.exists(resultados_folder_path):
            os.makedirs(resultados_folder_path)
        
        # add the folder name and the Urban_Model folder
        resultados_dir = os.path.join(resultados_folder_path, abrev, resultados_pred)
        if not os.path.exists(resultados_dir):
            os.makedirs(resultados_dir)
        
        # add the predictions folder and the visualizations folder
        make_predicciones = os.path.join(resultados_dir, predictions_folder)
        if not os.path.exists(make_predicciones):
            os.makedirs(make_predicciones)
            
        make_visualizacion = os.path.join(resultados_dir, visualizations_folder)
        if not os.path.exists(make_visualizacion):
            os.makedirs(make_visualizacion)

    # get audio files
    try:
        audio_files = [f for f in os.listdir(audio_path) if f.endswith(('.WAV', '.wav'))]
    except Exception as e:
        raise Exception(f"Error reading audio files: {e}")

    if not audio_files:
        raise Exception("No audio files found.")

    # get sample rate of the collection
    print("Getting sample rates of the audio files...")
    sample_rates = []
    valid_audio_files = []
    for file in audio_files:
        try:
            metadata = sf.info(os.path.join(audio_path,file))
            sample_rates.append(metadata.samplerate)
            valid_audio_files.append(file)
        except Exception as e:
            logging.error(f"Error reading file {file}: {e}")
    if not valid_audio_files:
        raise Exception("No valid audio files found.")

    sample_rates = np.array(sample_rates)

    if np.std(sample_rates) < 0.1:
        fs_model = np.median(sample_rates)
        logging.info('Todos los audios tienen una frecuencia de muestreo de  {} Hz'.format(np.median(sample_rates)))
    else:
        fs_model = np.median(sample_rates)
        logging.info('Los audios tienen una frecuencia de muestreo diferente, El modelo evaluara la frecuencia predominante {}'.format(fs_model))

    # allow growth 
    physical_devices = tf.config.experimental.list_physical_devices('GPU')
    for device in physical_devices:
        tf.config.experimental.set_memory_growth(device, True)

    try:
        print("Generating predictions...")
        data_df = get_predictions(audio_files=valid_audio_files,
                                  fs_model=fs_model,
                                  w_time=analysis_window_time,
                                  n_predictions=n_predictions)
    except Exception as e:
        raise Exception(f"Error generating predictions: {e}")

    logging.info(f"{len(valid_audio_files)} procesados")

    # csv File
    stable_version = get_stable_version()
    predictions_file = f'Urban_Model_{abrev}_{stable_version}_window_{args.window}s_test.csv'
    
    # save the predictions in a csv file
    data_df.to_csv(os.path.join(make_predicciones, predictions_file), index=False)
    logging.info(f"Archivo de prediciones creado en {os.path.abspath(os.path.join(make_predicciones, predictions_file))}")