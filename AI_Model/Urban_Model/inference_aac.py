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
import audio_metadata
import argparse

import params as yamnet_params
import yamnet as yamnet_model

import warnings

warnings.filterwarnings("ignore", category=RuntimeWarning, message="Couldn't find ffmpeg or avconv")
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

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


    def process_single_file(self, file_path, window_size=None, save_embeddings=False, save_spectrogram=False, save_clips=False):
        logging.info(f"Processing file: {file_path}")
        wav_data, sr = sf.read(file_path, dtype=np.int16)
        waveform = wav_data / 32768.0  # Convert to [-1.0, +1.0]
        waveform = waveform.astype('float32')

        # convert to mono and resemple if needed (different from 16kHz)
        if len(waveform.shape) > 1:
            waveform = np.mean(waveform, axis=1)
            logging.warning(f"Audio file has more than 1 channel. Taking the mean of all channels.")
        if sr != self.params.sample_rate:
            waveform = resampy.resample(waveform, sr, self.params.sample_rate)
            logging.warning(f"Resampling audio from {sr} to {self.params.sample_rate}")


        # process audio file
        predictions = []
        all_embeddings = []
        if window_size is None and save_clips is False:
            logging.info("Processing whole file without window size")
            logging.info(f"Waveform shape: {waveform.shape}")
            scores, embeddings, spectrogram = self.yamnet(waveform)

            if save_spectrogram:
                scores = scores.numpy()
                spectrogram = spectrogram.numpy()
                save_spectrogram_w_funct(spectrogram, scores, self.yamnet_classes, file_path, self.params.sample_rate)

            prediction = np.mean(scores, axis=0)
            predictions.append(prediction)

            if save_embeddings:
                all_embeddings.append(embeddings.numpy())
            return predictions, all_embeddings


        # process audio file with window size
        else:
            if save_spectrogram:
                logging.info("Entering the window size analysis. But we run the whole audio file to save the complteted spectrogram.")
                scores, embeddings, spectrogram = self.yamnet(waveform)
                scores = scores.numpy()
                spectrogram = spectrogram.numpy()
                save_spectrogram_w_funct(spectrogram, scores, self.yamnet_classes, file_path, self.params.sample_rate)

            if save_clips:
                window_size =  2.5
            logging.info(f"Processing file with window size: {window_size}")
            window_size_samples = int(window_size * sr)

            for start_idx in range(0, len(waveform), window_size_samples):
                end_idx = start_idx + window_size_samples
                if end_idx > len(waveform):
                    end_idx = len(waveform)  # include the last segment
            
                window = waveform[start_idx:end_idx]
                scores, embeddings, spectrogram = self.yamnet(window)
                
                if save_spectrogram:
                    scores = scores.numpy()
                    spectrogram = spectrogram.numpy()
                    save_spectrogram_w_funct(spectrogram, scores, self.yamnet_classes, file_path, self.params.sample_rate, start_idx, end_idx, window_size)

                prediction = np.mean(scores, axis=0)
                predictions.append(prediction)

                if save_embeddings:
                    all_embeddings.append(embeddings.numpy())

                if save_clips:
                    extrac_clips(prediction, window, start_idx, self.params.sample_rate,  self.yamnet_classes, file_path)
            return predictions, all_embeddings



def process_audio_files(classifier, base_path, window_size, threshold, stable_version, save_embeddings, save_spectrogram, save_clips):
    col_names = ['filename', 'date', 'class', 'probability']
    result_folder = folder_result(base_path)

    # looking for subfolders
    for subfolder in tqdm.tqdm(find_audiomoth_folders(base_path), desc='Processing subfolders'):
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


        # reading metadata
        sample_rates = []
        valid_audio_files = []
        logging.info(f"Reading metadata...")
        for file in tqdm.tqdm(audio_files[:1], desc='Reading metadata'):
            try:
                metadata = audio_metadata.load(os.path.join(audio_path, file))
                sample_rates.append(metadata.streaminfo.sample_rate)
                valid_audio_files.append(file)
            except Exception as e:
                logging.warning(f'Error reading file metadata: {file}, {e}')
        if not sample_rates:
            logging.warning("No valid audio files to process.")
            continue
        if not valid_audio_files:
            logging.warning(f"No valid audio files to process in {subfolder}")
            continue
        logging.info(f'Processing {len(valid_audio_files)} files in {subfolder}')


        # processing audio files
        all_data_subfolder = []
        for file_name in tqdm.tqdm(valid_audio_files, desc='Processing audio files'):
            try:
                full_path = os.path.join(audio_path, file_name)
                predictions_list, embeddings = classifier.process_single_file(full_path, window_size, save_embeddings, save_spectrogram, save_clips)

                if save_embeddings:
                    save_embeddings_funct(embeddings, subfolder_name, result_folder)

                name_split = file_name.split(".")[0]
                start_timestamp = datetime.datetime.strptime(name_split, '%Y%m%d_%H%M%S')

                threshold = classifier.params.classification_threshold if args.threshold is None else args.threshold
                logging.info(f"Classification threshold: {threshold}")

                for i, prediction in enumerate(predictions_list):
                    top_indices = np.argsort(prediction)[::-1][:3]
                    
                    filtered_classes = []
                    filtered_probabilities = []
                    for idx in top_indices:
                        if prediction[idx] >= threshold:
                            filtered_classes.append(classifier.yamnet_classes[idx])
                            filtered_probabilities.append(f'{prediction[idx]:.4f}')

                    filtered_classes_str = ', '.join(filtered_classes)
                    filtered_probabilities_str = ', '.join(filtered_probabilities)
                    # adjust timestamp based on window size
                    adjusted_timestamp = start_timestamp if window_size is None else start_timestamp + datetime.timedelta(seconds=i*window_size)

                    all_data_subfolder.append([
                        file_name, 
                        adjusted_timestamp.strftime('%Y-%m-%d %H:%M:%S'), 
                        filtered_classes_str, 
                        filtered_probabilities_str
                    ])

            except Exception as e:
                logging.error(f"Error processing file {file_name}: {e}")

        # save predictions to csv
        if all_data_subfolder:
            save_predictions_to_csv(all_data_subfolder, col_names, subfolder_name, result_folder, window_size, stable_version)
        else:
            logging.warning(f"No data to save for folder {subfolder}")



def parse_arguments():
    parser = argparse.ArgumentParser(description='Make prediction with YAMNet model for audio files in a directory')
    parser.add_argument('-p', '--path', type=str, required=True, help='Directory to be processed')
    parser.add_argument('-w', '--window', type=float, default=None, help='Window size in seconds for processing audio files. Default is None for processing full audio.')
    parser.add_argument('-t', '--threshold', type=float, default=None, help='Classification threshold for predictions.')
    parser.add_argument('--embeddings', action='store_true', help='Save embeddings to tensorboard')
    parser.add_argument('--spectrogram', action='store_true', help='Save spectrogram images')
    parser.add_argument('--clips', action='store_true', help='Save audio clips')
    return parser.parse_args()



if __name__ == '__main__':
    """
    python .\inference_aac.py -p "\\192.168.205.117\AAC_Server\OCIO\OCIO_BILBAO\CAMPAÑA_5"
    """
    setup_gpu()
    stable_version = get_stable_version()
    args = parse_arguments()
    
    # process audio files
    classifier = AudioClassifier()
    process_audio_files(classifier, args.path, args.window, args.threshold, stable_version, args.embeddings, args.spectrogram, args.clips)