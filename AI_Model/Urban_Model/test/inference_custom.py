from __future__ import division, print_function

import sys
import os
import numpy as np
import tqdm 
import resampy
import soundfile as sf
import tensorflow as tf
import csv

import params as yamnet_params
import yamnet as yamnet_model

physical_devices = tf.config.list_physical_devices('GPU')
print("Num GPUs Available: ", len(physical_devices))
for device in physical_devices:
    print(device)
if physical_devices:
    try:
        tf.config.experimental.set_memory_growth(physical_devices[0], True)
    except RuntimeError as e:
        print(e)

def process_audio_files(folder_path):
    params = yamnet_params.Params()
    yamnet = yamnet_model.yamnet_frames_model(params)
    yamnet.load_weights('yamnet.h5')
    yamnet_classes = yamnet_model.class_names('yamnet_class_map.csv')

    all_files = os.listdir(folder_path)
    wav_files = [file for file in all_files if file.lower().endswith('.wav')]
    
    # csv file to write the predictions
    with open('predictions.csv', 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['File Name', 'Class', 'Probability'])  # header

        for file_name in tqdm.tqdm(wav_files):
            try:
                full_path = os.path.join(folder_path, file_name)
                
                # decode wav file
                wav_data, sr = sf.read(full_path, dtype=np.int16)
                waveform = wav_data / 32768.0
                waveform = waveform.astype('float32')

                # convert to mono and sample rate
                if len(waveform.shape) > 1:
                    waveform = np.mean(waveform, axis=1)
                if sr != params.sample_rate:
                    waveform = resampy.resample(waveform, sr, params.sample_rate)

                # predict yamnet classes
                scores, embeddings, spectrogram = yamnet(waveform)
                prediction = np.mean(scores, axis=0)
                top5_i = np.argsort(prediction)[::-1][:5]
                print(f'{file_name} \t{yamnet_classes} \t{prediction:.3f}')

                # filter predictions below threshold and write to csv
                for i in top5_i:
                    if prediction[i] >= 0.35:
                        writer.writerow([file_name, yamnet_classes[i], f'{prediction[i]:.3f}'])
                        print(f'{file_name} \t{yamnet_classes[i]} \t{prediction[i]:.3f}')
            
            except Exception as e:  
                print(f"Error processing file {file_name}: {e}")

def main(argv):
    assert len(argv) == 1, 'Usage: inference_custom.py <folder containing wav files>'
    folder_path = argv[0]
    process_audio_files(folder_path)

if __name__ == '__main__':
    main(sys.argv[1:])
