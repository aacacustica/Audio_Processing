from __future__ import division, print_function

import os
import numpy as np
import tqdm
import resampy
import soundfile as sf
import tensorflow as tf
import logging
import datetime
import matplotlib.pyplot as plt
from utils import *
import audio_metadata

import params as yamnet_params
import yamnet as yamnet_model

logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s', 
    filename='yamnet_inference_test_threshold.log', 
    filemode='a'
)

class AudioClassifier:
    def __init__(self, threshold=None):
        self.params = yamnet_params.Params()
        self.yamnet = yamnet_model.yamnet_frames_model(self.params)
        self.yamnet.load_weights('yamnet.h5')
        self.yamnet_classes = yamnet_model.class_names('yamnet_class_map.csv')

        if threshold is not None:
            self.params.classification_threshold = threshold
            logging.info(f"Classification threshold set to: {threshold}")

    def process_single_file(self, file_path, window_size=None, save_embeddings=False, save_spectrogram=False):
        logging.info(f"Processing file: {file_path}")
        wav_data, sr = sf.read(file_path, dtype=np.int16)
        waveform = wav_data / 32768.0
        waveform = waveform.astype('float32')

        if len(waveform.shape) > 1:
            waveform = np.mean(waveform, axis=1)
            logging.warning(f"Audio file has more than 1 channel. Taking the mean of all channels.")
        if sr != self.params.sample_rate:
            waveform = resampy.resample(waveform, sr, self.params.sample_rate)
            logging.warning(f"Resampling audio from {sr} to {self.params.sample_rate}")

        predictions = []
        all_embeddings = []
        all_spectrograms = []

        if window_size is None:
            scores, embeddings, spectrogram = self.yamnet(waveform)
            predictions.append(np.mean(scores, axis=0))
            if save_embeddings:
                all_embeddings.append(embeddings.numpy())
            if save_spectrogram:
                all_spectrograms.append(spectrogram.numpy())
        else:
            window_size_samples = int(window_size * sr)
            for start_idx in range(0, len(waveform), window_size_samples):
                end_idx = start_idx + window_size_samples
                if end_idx > len(waveform):
                    break
                window = waveform[start_idx:end_idx]
                scores, embeddings, spectrogram = self.yamnet(window)
                predictions.append(np.mean(scores, axis=0))
                if save_embeddings:
                    all_embeddings.append(embeddings.numpy())
                if save_spectrogram:
                    all_spectrograms.append(spectrogram.numpy())

        return predictions, all_embeddings, all_spectrograms if save_spectrogram else predictions, all_embeddings

def process_audio_files(classifier, base_path, window_size, stable_version, save_embeddings, save_spectrogram):
    subfolders = [f.path for f in os.scandir(base_path) if f.is_dir()]
    col_names = ['filename', 'date', 'class', 'probability']
    result_folder = folder_result(base_path)

    for subfolder in tqdm.tqdm(subfolders, desc='Processing subfolders'):
        subfolder_name = os.path.basename(subfolder)
        audio_path = os.path.join(subfolder, "AUDIOMOTH")
        logging.info(f"Processing subfolder: {subfolder}...")

        if not os.path.exists(audio_path):
            logging.warning(f"Skipping {subfolder}, AUDIOMOTH folder not found.")
            continue

        audio_files = get_audiofiles(audio_path)
        if not audio_files:
            logging.warning(f"No audio files found in: {audio_path}")
            continue

        for file_name in tqdm.tqdm(audio_files, desc='Processing audio files'):
            full_path = os.path.join(audio_path, file_name)
            predictions, embeddings, spectrograms = classifier.process_single_file(
                full_path, window_size, save_embeddings, save_spectrogram
            )

            for i, (score, embedding, spectrogram) in enumerate(zip(predictions, embeddings, spectrograms)):
                save_spectrogram_funct(
                    spectrogram, score, classifier.yamnet_classes, 
                    file_name=os.path.basename(file_name).split('.')[0], 
                    window_index=i, result_folder=result_folder
                )

if __name__ == '__main__':
    gpus = tf.config.experimental.list_physical_devices('GPU')
    if gpus:
        try:
            for gpu in gpus:
                tf.config.experimental.set_memory_growth(gpu, True)
                logging.info(f"Enabled memory growth for {gpu.name}")
        except RuntimeError as e:
            logging.error(f"Failed to set memory growth: {e}")

    setup_gpu()
    stable_version = get_stable_version()
    args = parse_arguments()
    
    classifier = AudioClassifier(threshold=args.threshold)
    process_audio_files(classifier, args.path, args.window_size, stable_version, args.embeddings, args.spectrogram)