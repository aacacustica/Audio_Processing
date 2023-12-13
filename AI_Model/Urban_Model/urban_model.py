import json
import numpy as np
import soundfile as sf
from scipy.signal import medfilt
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
                    filename='urban_model.log',
                    )


# get the last git tag version
def list_git_tags():
    try:
        tags = tags = subprocess.check_output(["git", "tag"]).strip().decode()
        return tags.split('\n')
    except subprocess.CalledProcessError:
        return None
    
def select_tag(tags):
    for i, tag in enumerate(tags):
        print(f"{i}: {tag}")
    choice = int(input("Select the tag to use: "))
    
    return tags[choice]

def audios_long(audio_files):
    """Print how long the audio files are.
    Args:
        audio_files (list): List of audio files to be analyzed.
    
    Returns:
        None
    """
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
    """Prints the audio time.
    Args:
        w_size (int): Analysis window size.
        sr (int): Sampling frequency.
        wav_data (list): Audio data.
    
    Returns:
        None
    """
    # Audio time length
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



def get_predictions(audio_files:list, fs_model:float, w_time:int, taxonomy_mapping:dict, n_predictions:int):
    """Get predictions from yamnet model in a collection of audio files averaged over an analysis window and map to custom classes.
    Args:
        audio_files (list): List of audio files to be analyzed.
        fs_model (float): Sampling frequency of the model.
        w_time (int): Analysis window size in minutes.
        taxonomy_mapping (dict): Mapping from original classes to custom classes.
        n_predictions (int): Number of predictions to be generated.
    
    Returns:
        df_sorted (pd.DataFrame): Dataframe with the predictions.

    trafico, gente y 
    """
    params.PATCH_HOP_SECONDS = 1 # 1 Hz frame rate.
    params.SAMPLE_RATE = int(fs_model) # Sampling frequency.
    logging.info(f"Model configured with fs= {int(fs_model)}")
    
    yamnet = yamnet_model.yamnet_frames_model(params)
    yamnet.load_weights('yamnet.h5')
    class_names = yamnet_model.class_names('yamnet_class_map.csv')

    audio_classes = []
    audio_classes_original = [] 
    probs = []
    probs_original = [] 
    datetimes = []
    files = []
    # audio_to_process = 10

    # for file in tqdm(audio_files[:audio_to_process]):
    for file in tqdm(audio_files):
        logging.info(f"Processing audio file  -->  {file}")
        
        # wav_data, sr = sf.read(os.path.join(audio_path, file), dtype=np.int16)
        try:
            wav_data, sr = sf.read(os.path.join(audio_path, file), dtype=np.int16)
        except Exception as e:
            logging.error(f"Failed to read file {file}: {e}")
            continue
        
        waveform = wav_data / 32768.0  # 2**15
        # w_size = int(w_time * 60 * sr)
        # w_size = w_time * 60 * sr
        w_size = int(round(14.99 * 60 * sr))
        
        print_audio_time(w_size, sr, wav_data)      

        count = 0
        if len(waveform) > w_size:
            for fstart in range(0, len(waveform) - w_size + 1, w_size):


                # GETTING THE SCORES FOR THE CUSTOM TAXONOMY

                # getting the scores for the original taxonomy
                # to to that, we need to reshape the waveform to [1, -1] and predict, [to get the values of the prediction fdrom 0 to 1] then average the scores over the frames
                scores, _ = yamnet.predict(np.reshape(waveform[fstart:fstart+w_size], [1, -1]), steps=1)
                prediction = np.mean(scores, axis=0)

                # top_original = np.argsort(prediction)[::-1][:5]
                # get the top n predictions
                top_original = np.argsort(prediction)[::-1][:n_predictions]

                # [1] get the classes and probabilities for the original taxonomy
                clip_classes_original = [class_names[i] for i in top_original]
                prob_classes_original = [prediction[i] for i in top_original]

                # append to the lists
                audio_classes_original.append(clip_classes_original)
                probs_original.append(prob_classes_original)


                # [2] adjust scores based on the new taxonomy

                # new_scores is a dictionary with the new classes as keys and the scores as values
                new_scores = {key: 0 for key in set(taxonomy_mapping.values())}
                # we go through the original classes and add the scores to the new classes
                for original_class, mapped_class in taxonomy_mapping.items():
                    # get the index of the original class in the original taxonomy
                    index = np.where(class_names == original_class)[0][0]
                    # add the score to the new class
                    new_scores[mapped_class] += prediction[index]
    


                # NORMALIZE THE SCORES

                # normalize the scores
                total_score = sum(new_scores.values())
                for key in new_scores:
                    new_scores[key] /= total_score
                
                # get the top n predictions, sorted in descending order
                top_i = np.argsort(list(new_scores.values()))[::-1][:n_predictions]

                # [3] we want to order the classes and probabilities by date
                date = datetime.datetime.strptime(file.split('.')[0], '%Y%m%d_%H%M%S')
                date = date + datetime.timedelta(minutes=w_time * count)
                datetimes.append(date)


                # [4] SAVE THE CUSTOM CLASSES AND PROBABILITIES
                clip_classes = []
                prob_classes = []

                for i in top_i:
                    clip_classes.append(list(new_scores.keys())[i])
                    prob_classes.append(list(new_scores.values())[i])

                # APPLY THE THRESHOLD TO GET CLEANER PREDICTIONS
                if prob_classes:
                    prob_classes = medfilt(prob_classes, kernel_size=3)
                    pass


                audio_classes.append(clip_classes)
                probs.append(prob_classes)
                files.append(file)
                
                if len(clip_classes) == 1:
                    logging.info(f"We are adding 1 class for window analysis.")
                else:
                    logging.info(f"We are adding {len(clip_classes)} classes for window analysis.")
                
        else:
            logging.warning("Audio shorter than analysis window")


    # SAVE THE PREDICTIONS IN A (DICT) DATAFRAME
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
    parser.add_argument('-p', '--path', required=True, type=str, help='Path to the audio files')
    parser.add_argument('-a', '--abrev', type=str, help='Name to identify the predictions file')
    parser.add_argument('-w', '--window', type=float, default=14.99, help='tamaño ventana de analisis en minutos')
    parser.add_argument('-n', '--n-predictions', type=int, default=3, help='Number of predictions to be generated')
    parser.add_argument('-r', '--result-folder', type=str, default=None, help='Location where the results should be saved')
    args = parser.parse_args()
    return args

if __name__ == "__main__":
    args = argument_parser()
    
    # set the version tag
    tags = list_git_tags()
    version_tag = select_tag(tags)
    logging.info(f"Version tag: {version_tag}")

    # set path to audio files
    audio_path = args.path

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
    else:
        parent_dir = os.path.dirname(audio_path)
        results_folder = "Results/Urban_Model/Predictions"  
        # check if the results folder exists, if not, create it
        results_dir = os.path.join(parent_dir, results_folder)
        os.makedirs(results_dir, exist_ok=True)
        
        logging.info(f"Carpeta de resultados creada en {os.path.abspath(results_dir)}")

    
    # get audio files
    try:
        audio_files = [f for f in os.listdir(audio_path) if f.endswith(('.WAV', '.wav'))]
    except Exception as e:
        raise Exception(f"Error reading audio files: {e}")

    if not audio_files:
        raise Exception("No audio files found.")

    # get sample rate of the collection
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

    with open('taxonomy_mapping_v1.0.json', 'r') as f:
        taxonomy_mapping = json.load(f)

    try:
        data_df = get_predictions(audio_files=valid_audio_files,
                                  fs_model=fs_model,
                                  w_time=analysis_window_time,
                                  taxonomy_mapping=taxonomy_mapping,
                                  n_predictions=n_predictions)
    except Exception as e:
        raise Exception(f"Error generating predictions: {e}")

    logging.info(f"{len(valid_audio_files)} procesados")

    # csv File
    version_tag = version_tag.replace('.', '_')
    predictions_file = f'Urban_Model_{abrev}_{version_tag}.csv'
    data_df.to_csv(os.path.join(results_dir, predictions_file), index=False)

    logging.info(f"Archivo de prediciones creado en {os.path.abspath(os.path.join(results_folder,predictions_file))}")

