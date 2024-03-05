import os
import numpy as np
import pandas as pd
from tqdm import tqdm
import datetime

import soundfile as sf
import argparse
import re


import params
import yamnet as yamnet_model
import tensorflow as tf

import logging

tf.get_logger().setLevel(logging.ERROR)

logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s', 
                    filename='execution_time.log',
                    )


def get_predictions(audio_files:list, fs_model:float, w_time:int, n_predictions:int):
    params.PATCH_HOP_SECONDS = 1 # 1 Hz frame rate
    params.SAMPLE_RATE = int(fs_model) 
    logging.info(f"Model confifured with {params.PATCH_HOP_SECONDS} Hz frame rate")
    logging.info(f"Model configured with fs= {int(fs_model)}")
    
    yamnet = yamnet_model.yamnet_frames_model(params)
    yamnet.load_weights('yamnet.h5')
    class_names = yamnet_model.class_names('yamnet_class_map.csv')
    logging.info(f"YAMNet model loaded with {len(class_names)} classes")
    
    classes = [] 
    probabilities = [] 
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
        w_size = int(w_time * sr)
        # w_size = int(w_time * 60 * sr)
        
        try:
            match = re.search(r'(\d{8}_\d{6})', file.split('.')[0])
            if match:
                date_str = match.group(1)  # Extract the datetime part
                start_datetime = datetime.datetime.strptime(date_str, '%Y%m%d_%H%M%S')
            else:
                logging.info(f"Non-standard file name, skipping datetime extraction: {file}")
                start_datetime = datetime.datetime.now()
        except ValueError as e:
            logging.error(f"Error parsing datetime from file name {file}: {e}")
            start_datetime = datetime.datetime.now()  # Use current time as a fallback
        
        # start the log
        inference_start_time = datetime.datetime.now()

        if len(waveform) > w_size:
            for count, fstart in enumerate(range(0, len(waveform) - w_size + 1, w_size)):
                # get the predictions
                scores, spectrogram = yamnet.predict(np.reshape(waveform[fstart:fstart+w_size], [1, -1]), steps=1)
                prediction = np.mean(scores, axis=0)
                # add spectrogram
                spectrograms.append(spectrogram)

                # get the top n predictions
                top_classes = np.argsort(prediction)[::-1][:n_predictions]

                # get the classes and probabilities for the original taxonomy
                clip_classes = [class_names[i] for i in top_classes]
                prob_classes = [prediction[i] for i in top_classes]

                # append to the lists
                classes.append(clip_classes)
                probabilities.append(prob_classes)
                        
                # set time column
                window_datetime = start_datetime + datetime.timedelta(seconds=w_time * count)
                datetimes.append(window_datetime)

                # append file
                files.append(file) 
                
                inference_end_time = datetime.datetime.now()
                inference_duration = inference_end_time - inference_start_time
                logging.info(f"Inference for {file} took {inference_duration.total_seconds()} seconds.")

        else:
            logging.warning("Audio shorter than analysis window")

    # save the results in a dataframe
    data_dict = {'file': files, 
                 'datetime': datetimes, 
                 'classes_original': classes, 
                 'probabilities_original': probabilities,
                #  'spectrograms': spectrograms
                
                 } 

    # sort by datetime in ascending order
    df = pd.DataFrame(data_dict)
    # df_sorted = df.sort_values(by='datetime')
    df_sorted = df.sort_values(by='file')

    return df_sorted

def argument_parser():
    parser = argparse.ArgumentParser(description='Inferencia Yamnet de todos los archivos de audio en un directorio')
    parser.add_argument('-p', '--path', required=True, type=str, help='Path to the audio files')
    parser.add_argument('-w', '--window', type=float, default=899, help='Analysis window size in seconds')
    parser.add_argument('-n', '--n-predictions', type=int, default=3, help='Number of predictions to be generated')
    parser.add_argument('-r', '--result-folder', type=str, default=None, help='Location where the results should be saved')
    args = parser.parse_args()
    return args

if __name__ == "__main__":
    """
    example of use:
            python EverSmartScript.py -p /home/usuario/audios -a "audios_1" -w 14.99 -n 3 -r /home/usuario/resultados
    """
    args = argument_parser()
    # set path to audio files
    audio_path = args.path
    # set analysis window size in minutes
    analysis_window_time = args.window
    # set number of predictions
    n_predictions = args.n_predictions
    
    # set results folder
    if args.result_folder:
        results_dir = args.result_folder
        results_dir = os.path.join(results_dir, 'YAMet_results')
        if not os.path.exists(results_dir):
            os.makedirs(results_dir)
        make_predicciones = results_dir
    else:
        results_dir = os.path.join(os.getcwd(), 'YAMet_results')
        if not os.path.exists(results_dir):
            os.makedirs(results_dir)
            
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
    else:
        fs_model = np.median(sample_rates)

    # get predictions
    try:
        data_df = get_predictions(audio_files=valid_audio_files,
                                  fs_model=fs_model,
                                  w_time=analysis_window_time,
                                  n_predictions=n_predictions)
    except Exception as e:
        raise Exception(f"Error generating predictions: {e}")
    
    predictions_file = f'YAMNet_Predictions_w_{args.window}s.csv'
    data_df.to_csv(os.path.join(make_predicciones, predictions_file), index=False)