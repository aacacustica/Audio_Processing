from __future__ import division, print_function

import sys
import os
import numpy as np
import tqdm 
import resampy
import soundfile as sf
import tensorflow as tf
import csv
import logging
from utils import *

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


def process_audio_files(classifier, folder_path):
    all_files = os.listdir(folder_path)
    wav_files = [file for file in all_files if file.lower().endswith('.wav')]

    with open('predictions.csv', 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['filename', 'class', 'probability'])  # header

        for file_name in tqdm.tqdm(wav_files):
            try:
                full_path = os.path.join(folder_path, file_name)
                waveform, prediction = classifier.process_single_file(full_path)
                write_predictions(writer, file_name, prediction, classifier.yamnet_classes)
            except Exception as e:
                print(f"Error processing file {file_name}: {e}")


def write_predictions(writer, file_name, prediction, yamnet_classes):
    top5_i = np.argsort(prediction)[::-1][:5]

    classes = []
    probabilities = []
    for i in top5_i:
        print(f'{file_name} \t{yamnet_classes[i]} \t{prediction[i]:.3f}')
        if prediction[i] >= 0.30:
            classes.append(yamnet_classes[i])
            probabilities.append(f'{prediction[i]:.3f}')           

    row = [file_name] + classes + probabilities
    writer.writerow(row)

if __name__ == '__main__':
    import sys
    assert len(sys.argv) == 2, 'Usage: script.py <folder containing wav files>'
    folder_path = sys.argv[1]
    setup_gpu()
    classifier = AudioClassifier()
    process_audio_files(classifier, folder_path)