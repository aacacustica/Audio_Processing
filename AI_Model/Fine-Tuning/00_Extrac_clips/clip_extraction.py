from __future__ import division, print_function

import os
import numpy as np
import tqdm
import resampy
import soundfile as sf
import logging
from utils import *
import datetime
import audio_metadata
import argparse
import hashlib
import time

import params as yamnet_params
import yamnet as yamnet_model
import warnings

warnings.filterwarnings("ignore", category=RuntimeWarning, message="Couldn't find ffmpeg or avconv")
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s', 
    filename='clip_extraction.log', 
    filemode='a'
    )


class AudioClassifier:
    def __init__(self):
        self.params = yamnet_params.Params()
        self.yamnet = yamnet_model.yamnet_frames_model(self.params)
        self.yamnet.load_weights('yamnet.h5')
        self.yamnet_classes = yamnet_model.class_names('yamnet_class_map.csv')


    def process_single_file(self, file_path, window_size=5, save_embeddings=False, save_spectrogram=False):
        logging.info(f"Processing file: {file_path}")
        logging.info(f"Classification threshold: {self.params.classification_threshold}")
        
        wav_data, sr = sf.read(file_path, dtype=np.int16)
        waveform = wav_data / 32768.0
        waveform = waveform.astype('float32')

        if len(waveform.shape) > 1:
            waveform = np.mean(waveform, axis=1)
        if sr != self.params.sample_rate:
            waveform = resampy.resample(waveform, sr, self.params.sample_rate)

        all_embeddings = []
        all_data = []

        window_size_samples = int(window_size * self.params.sample_rate)
        for start_idx in range(0, len(waveform), window_size_samples):
            # get end index of window
            end_idx = min(start_idx + window_size_samples, len(waveform))

            # make prediction for each window
            window = waveform[start_idx:end_idx]
            scores, embeddings, spectrogram = self.yamnet(window)

            # save spectrograms
            if save_spectrogram:
                    scores = scores.numpy()
                    spectrogram = spectrogram.numpy()
                    save_spectrogram_w_funct(spectrogram, scores, self.yamnet_classes, file_path, self.params.sample_rate, start_idx, end_idx, window_size)

            # filter predictions
            prediction = np.mean(scores, axis=0)
            top_classes = np.argsort(prediction)[::-1][:2]
            filtered_classes = [i for i in top_classes if prediction[i] > self.params.classification_threshold]
            if not filtered_classes:
                logging.info(f"No classes above threshold in window")
                continue

            # making predictions folder
            save_path = file_path.replace("3-Medidas", "5-Resultados")
            if "AUDIOMOTH" in save_path:
                save_path = save_path.split("AUDIOMOTH")[0]

                folder_name = save_path.split("\\")
                if folder_name[-1] == "":
                    folder_name = folder_name[-2]

                save_path = os.path.join(save_path, "AI_MODEL", "Training_clips")
            os.makedirs(save_path, exist_ok=True)

            # save clips
            for i in filtered_classes:
                class_name = self.yamnet_classes[i].replace(" ", "_")
                # using a hash to generate a unique id for the clip
                unique_id = hashlib.sha256(f"{file_path}{time.time()}".encode()).hexdigest()[:10]
                # setting filename
                filename = f"{unique_id}_{class_name}.wav"
                clip_path = os.path.join(save_path, filename)
                # saving clip
                sf.write(file=clip_path, data=window, samplerate=sr)
                # saving csv data
                all_data.append([filename, self.yamnet_classes[i], prediction[i]])

            if save_embeddings:
                all_embeddings.append(embeddings.numpy())

        return all_data, save_path, folder_name



def process_audio_files(classifier, base_path, stable_version, save_embeddings, save_spectrogram, window_size):
    # looking for subfolders
    audiomoth_folders = list(find_audiomoth_folders(base_path))
    for subfolder in tqdm.tqdm(audiomoth_folders, desc='Processing subfolders'):
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
        logging.info("")
        logging.info(f"Reading metadata...")
        for file in tqdm.tqdm(audio_files[:2], desc='Reading metadata'):
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
        for file_name in tqdm.tqdm(valid_audio_files, desc='Processing audio files'):
            full_path = os.path.join(audio_path, file_name)
            try:
                classifier.process_single_file(full_path, window_size, save_embeddings, save_spectrogram)
            except Exception as e:
                logging.error(f"Error processing file {file_name}: {e}")


def parse_arguments():
    parser = argparse.ArgumentParser(description='Make prediction with YAMNet model for audio files in a directory')
    parser.add_argument('-p', '--path', type=str, required=True, help='Directory to be processed')
    parser.add_argument('--embeddings', action='store_true', help='Save embeddings to tensorboard')
    parser.add_argument('--spectrogram', action='store_true', help='Save spectrogram images')
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
    process_audio_files(classifier, args.path, stable_version, args.embeddings, args.spectrogram, window_size=5)

    logging.info("Inference finished.")