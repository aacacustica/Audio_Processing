from __future__ import division, print_function

import os
import numpy as np
import tqdm
import resampy
import soundfile as sf
import tensorflow as tf
import logging
from utils import *
import datetime

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

    def process_single_file(self, file_path, window_size=None):
        logging.info(f"Processing file: {file_path}")
        wav_data, sr = sf.read(file_path, dtype=np.int16)
        waveform = wav_data / 32768.0  # Normalize audio
        waveform = waveform.astype('float32')

        if len(waveform.shape) > 1:
            waveform = np.mean(waveform, axis=1)
            logging.warning(f"Audio file has more than 1 channel. Taking the mean of all channels.")
        if sr != self.params.sample_rate:
            waveform = resampy.resample(waveform, sr, self.params.sample_rate)
            logging.warning(f"Resampling audio from {sr} to {self.params.sample_rate}")

        if window_size is None:
            logging.info("Processing whole file without window size")
            scores, embeddings, spectrogram = self.yamnet(waveform)
            prediction = np.mean(scores, axis=0)
            return [prediction]

        else:
            logging.info(f"Processing file with window size: {window_size}")
            window_size_samples = int(window_size * sr)
            predictions = []
            for start_idx in range(0, len(waveform), window_size_samples):
                end_idx = start_idx + window_size_samples
                if end_idx > len(waveform):
                    break
                window = waveform[start_idx:end_idx]
                scores, embeddings, spectrogram = self.yamnet(window)
                prediction = np.mean(scores, axis=0)
                predictions.append(prediction)
            return predictions

        
def process_audio_files(classifier, base_path, window_size):
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
                predictions_list = classifier.process_single_file(full_path, window_size)

                name_split = file_name.split(".")[0]
                start_timestamp = datetime.datetime.strptime(name_split, '%Y%m%d_%H%M%S')

                # classification threshold
                threshold = classifier.params.classification_threshold

                for i, prediction in enumerate(predictions_list):
                    top_indices = np.argsort(prediction)[::-1][:5]
                    print_top_predictions(file_name, prediction, classifier.yamnet_classes, top_n=5)
                    
                    filtered_classes = []
                    filtered_probabilities = []
                    for idx in top_indices:
                        if prediction[idx] >= threshold:
                            filtered_classes.append(classifier.yamnet_classes[idx])
                            filtered_probabilities.append(f'{prediction[idx]:.4f}')

                    filtered_classes_str = ', '.join(filtered_classes)
                    filtered_probabilities_str = ', '.join(filtered_probabilities)

                    adjusted_timestamp = start_timestamp if window_size is None else start_timestamp + datetime.timedelta(seconds=i*window_size)

                    all_data_subfolder.append([
                        file_name, 
                        adjusted_timestamp.strftime('%Y-%m-%d_%H:%M:%S'), 
                        filtered_classes_str, 
                        filtered_probabilities_str
                    ])

            except Exception as e:
                logging.error(f"Error processing file {file_name}: {e}")

        if all_data_subfolder:
            save_predictions_to_csv(all_data_subfolder, col_names, subfolder_name, result_folder, window_size)
        else:
            logging.warning(f"No data to save for folder {subfolder}")


if __name__ == '__main__':
    setup_gpu()
    args = parse_arguments()
    folder_path = args.path
    window_size = args.window_size
    classifier = AudioClassifier()
    process_audio_files(classifier, folder_path, window_size)