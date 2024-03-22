from __future__ import division, print_function

import sys
import os
import numpy as np
import resampy
import soundfile as sf
import tensorflow as tf

import params as yamnet_params
import yamnet as yamnet_model

def process_audio_files(folder_path):
    params = yamnet_params.Params()
    yamnet = yamnet_model.yamnet_frames_model(params)
    yamnet.load_weights('yamnet.h5')
    yamnet_classes = yamnet_model.class_names('yamnet_class_map.csv')

    all_files = os.listdir(folder_path)
    wav_files = [file for file in all_files if file.lower().endswith('.wav')]

    for file_name in wav_files:
        full_path = os.path.join(folder_path, file_name)
        # Decode the WAV file.
        wav_data, sr = sf.read(full_path, dtype=np.int16)
        print(f"\nsr: {sr}")
        assert wav_data.dtype == np.int16, 'Bad sample type: %r' % wav_data.dtype
        waveform = wav_data / 32768.0  # Convert to [-1.0, +1.0]
        waveform = waveform.astype('float32')

        # Convert to mono and the sample rate expected by YAMNet.
        if len(waveform.shape) > 1:
            waveform = np.mean(waveform, axis=1)
        if sr != params.sample_rate:
            waveform = resampy.resample(waveform, sr, params.sample_rate)
            # print the new sr
            print(f"new sr: {params.sample_rate} doe {file_name}")

        # Predict YAMNet classes.
        scores, embeddings, spectrogram = yamnet(waveform)
        prediction = np.mean(scores, axis=0)
        top5_i = np.argsort(prediction)[::-1][:5]
        print(full_path, ':\n' +
              '\n'.join('  {:12s}: {:.3f}'.format(yamnet_classes[i], prediction[i])
                        for i in top5_i))

def main(argv):
    print("Hey")
    assert len(argv) == 1, 'Usage: inference_custom.py <folder containing wav files>'
    folder_path = argv[0]
    process_audio_files(folder_path)

if __name__ == '__main__':
    main(sys.argv[1:])
