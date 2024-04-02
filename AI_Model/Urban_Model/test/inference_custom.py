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

# Check if TensorFlow can access the GPU
physical_devices = tf.config.list_physical_devices('GPU')
print("Num GPUs Available: ", len(physical_devices))
for device in physical_devices:
    print(device)

# Enable memory growth for a specific GPU
if physical_devices:
    try:
        # Prevent TensorFlow from using all the GPU memory
        tf.config.experimental.set_memory_growth(physical_devices[0], True)
    except RuntimeError as e:
        # Memory growth must be set before initializing GPUs
        print(e)

def process_audio_files(folder_path):
    params = yamnet_params.Params()
    yamnet = yamnet_model.yamnet_frames_model(params)
    yamnet.load_weights('yamnet.h5')
    yamnet_classes = yamnet_model.class_names('yamnet_class_map.csv')

    all_files = os.listdir(folder_path)
    wav_files = [file for file in all_files if file.lower().endswith('.wav')]
    
    # Open a CSV file to write the predictions
    with open('predictions.csv', 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['File Name', 'Class', 'Probability'])  # Write the header

        for file_name in tqdm.tqdm(wav_files):
            full_path = os.path.join(folder_path, file_name)
            
            # Decode the WAV file
            wav_data, sr = sf.read(full_path, dtype=np.int16)
            waveform = wav_data / 32768.0
            waveform = waveform.astype('float32')

            # Convert to mono and the sample rate expected by YAMNet
            if len(waveform.shape) > 1:
                waveform = np.mean(waveform, axis=1)
            if sr != params.sample_rate:
                waveform = resampy.resample(waveform, sr, params.sample_rate)

            # Predict YAMNet classes
            scores, embeddings, spectrogram = yamnet(waveform)
            prediction = np.mean(scores, axis=0)
            top5_i = np.argsort(prediction)[::-1][:5]

            # Filter predictions below threshold and write to CSV
            for i in top5_i:
                if prediction[i] >= 0.35:
                    writer.writerow([file_name, yamnet_classes[i], f'{prediction[i]:.3f}'])
                    print(f'{file_name} \t{yamnet_classes[i]} \t{prediction[i]:.3f}')

def main(argv):
    assert len(argv) == 1, 'Usage: inference_custom.py <folder containing wav files>'
    folder_path = argv[0]
    process_audio_files(folder_path)

if __name__ == '__main__':
    main(sys.argv[1:])
