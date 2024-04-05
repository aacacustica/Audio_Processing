from __future__ import division, print_function

import sys
import os
import numpy as np
import tqdm
import resampy
import soundfile as sf
import tensorflow as tf
import logging
from utils import *
import datetime
import pandas as pd

import params as yamnet_params
import yamnet as yamnet_model

logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s', 
    filename='yamnet_inference.log', 
    filemode='a'
    )

class AudioClassifier:
    def __init__(self):
        self.params = yamnet_params.Params()
        self.yamnet = yamnet_model.yamnet_frames_model(self.params)
        self.yamnet.load_weights('yamnet.h5')
        self.yamnet_classes = yamnet_model.class_names('yamnet_class_map.csv')

    def process_single_file(self, file_path):
        wav_data, sr = sf.read(file_path, dtype=np.int16)
        waveform = wav_data / 32768.0
        waveform = waveform.astype('float32')

        if len(waveform.shape) > 1:
            waveform = np.mean(waveform, axis=1)
        if sr != self.params.sample_rate:
            waveform = resampy.resample(waveform, sr, self.params.sample_rate)

        scores, embeddings, spectrogram = self.yamnet(waveform)
        prediction = np.mean(scores, axis=0)
        return waveform, prediction


def process_audio_files(classifier, base_path):
    subfolders = [f.path for f in os.scandir(base_path) if f.is_dir()]
    col_names = ['Filename', 'Time', 'Class', 'Probability']
    result_folder = folder_result(base_path)

    for subfolder in tqdm.tqdm(subfolders, desc='Processing subfolders'):
        subfolder_name = os.path.basename(subfolder)
        audio_path = os.path.join(subfolder, "AUDIOMOTH")
        logging.info(f"Processing subfolder: {subfolder}...")

        if not os.path.exists(audio_path):
            logging.warning(f"Skipping {subfolder}, AUDIOMOTH folder not found.")
            continue

        audio_files = [file for file in os.listdir(audio_path) if file.lower().endswith('.wav')]
        if not audio_files:
            logging.warning(f"No audio files found in: {audio_path}")
            continue

        all_data_subfolder = []
        for file_name in audio_files:
            try:
                full_path = os.path.join(audio_path, file_name)
                waveform, prediction = classifier.process_single_file(full_path)

                # sort predictions
                top_indices = np.argsort(prediction)[::-1]
                filtered_classes = []
                filtered_probabilities = []
                for idx in top_indices:
                    if prediction[idx] >= 0.3:  # Threshold check
                        filtered_classes.append(classifier.yamnet_classes[idx])
                        filtered_probabilities.append(f'{prediction[idx]:.4f}')
                
                # join the classes and probabilities
                filtered_classes_str = ', '.join(filtered_classes)
                filtered_probabilities_str = ', '.join(filtered_probabilities)

                name_split = file_name.split(".")[0]
                start_timestamp = datetime.datetime.strptime(name_split, '%Y%m%d_%H%M%S')

                all_data_subfolder.append([file_name, start_timestamp.strftime('%Y-%m-%d_%H:%M:%S'), filtered_classes_str, filtered_probabilities_str])

            except Exception as e:
                logging.error(f"Error processing file {file_name}: {e}")

        if all_data_subfolder:
            save_predictions_to_csv(all_data_subfolder, col_names, subfolder_name, result_folder)
        else:
            logging.warning(f"No data to save for folder {subfolder}")

if __name__ == '__main__':
    args = parse_arguments()
    folder_path = args.path
    setup_gpu()
    classifier = AudioClassifier()
    process_audio_files(classifier, folder_path)