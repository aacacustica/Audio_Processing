import pandas as pd
import matplotlib.pyplot as plt
from scipy.signal import find_peaks
import os
from datetime import datetime
from pydub import AudioSegment
from tqdm import tqdm
import numpy as np
import soundfile as sf
import resampy
import warnings
import math

import params as yamnet_params
import yamnet as yamnet_model

# warning messages disabled
warnings.filterwarnings("ignore", category=RuntimeWarning, message="Couldn't find ffmpeg or avconv")
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

WINDOW_SIZE = 30  # seconds
PROMINENCE = 1
WIDTH = 1
NUM_POINTS = 5
CLIP_DURATION = 5  # seconds


def make_clip_predictions(waveform, sr):
    params = yamnet_params.Params()
    yamnet = yamnet_model.yamnet_frames_model(params)
    yamnet.load_weights('yamnet.h5')
    yamnet_classes = yamnet_model.class_names('yamnet_class_map.csv')

    # convert to mono and resample if necessary
    if len(waveform.shape) > 1:
        waveform = np.mean(waveform, axis=1)
    if sr != params.sample_rate:
        waveform = resampy.resample(waveform, sr, params.sample_rate)

    # actual prediction
    scores, embeddings, spectrogram = yamnet(waveform)
    prediction = np.mean(scores, axis=0)
    # top 3 classes
    top3_i = np.argsort(prediction)[::-1][:3]
    print(f"Top 3 classes: {top3_i}")
    return [yamnet_classes[i] for i in top3_i], [prediction[i] for i in top3_i]



def extract_and_predict(filename, start_time, end_time, duration):
    print(f"Extracting segment from {filename}")
    # read the entire audio file
    wav_data, sr = sf.read(filename, dtype=np.int16)
    
    # calculate the start and end indices relative to the start of the recording
    datetime_string = filename.split('\\')[-1].split('_')
    date_part = datetime_string[0]  # '20231211'
    time_part = datetime_string[1].split('.')[0]  # '140420'
    recording_start_time = datetime.strptime(date_part + time_part, '%Y%m%d%H%M%S')
    
    print(f"Recording start time: {recording_start_time}")
    start_seconds = (start_time - recording_start_time).total_seconds()
    end_seconds = (end_time - recording_start_time).total_seconds()

    # math.ceil to ensure you cover the entire duration
    start_index = int(start_seconds * sr)
    end_index = int(math.ceil(end_seconds * sr))
    
    # Additional diagnostic outputs
    print(f"File sample rate: {sr}, Total samples: {len(wav_data)}")
    print(f"Calculated start seconds: {start_seconds}, end seconds: {end_seconds}")
    print(f"Expected segment duration: {end_seconds - start_seconds} seconds")
    print(f"Start index: {start_index}, End index: {end_index}")
    print(f"Start index in seconds {start_index / sr} End index in seconds: {end_index / sr}")
    print(f"Duration of seconds {end_index / sr - start_index / sr}")
    print(f"Original Duration: {duration} seconds")
    
    # indices are within valid range
    if start_index < 0 or end_index <= start_index or start_index >= len(wav_data) or end_index > len(wav_data):
        print(f"Invalid indices or out of bounds: Start index: {start_index}, End index: {end_index}")
        return None, None

    # extract the actual segment
    segment = wav_data[start_index:end_index]
    actual_segment_duration = len(segment) / sr
    print(f"Segment duration: {actual_segment_duration} seconds")

    wave_form = segment / 32768.0  # Convert to [-1.0, +1.0]
    wave_form = wave_form.astype('float32')
    print(f"Duration: {len(wave_form) / sr} seconds\n")

    # check if segment is valid
    # if len(segment) > 0:
    #     # normalize the segment to float32 for the prediction model
    #     waveform = segment / 32768.0  # Convert to [-1.0, +1.0]
    #     waveform = waveform.astype('float32')
        # exit()

        # make predictions
        # classes, probabilities = make_clip_predictions(waveform, sr)

        # segment_filename = filename.replace(".WAV", f"_{start_time.strftime('%H%M%S')}_{classes[0]}.WAV")
        # sf.write(segment_filename, segment, sr)
    
    # else:
    #     print("Invalid segment")


def main():
    csv_file = r"\\192.168.205.117\AAC_Server\PUERTOS\NOISEPORT\20231211_SANTUR\5-Resultados\P1_CONTENEDORES\SPL\leq_levels_P1_CONTENEDORES_v1_1_test.csv"
    title = csv_file.split("\\")[-3]
    audiomoth_folder = csv_file.replace("5-Resultados", "3-Medidas").replace("SPL", "AUDIOMOTH")
    audiomoth_folder = "\\".join(audiomoth_folder.split("\\")[:-1])
    output_folder = "\\".join(csv_file.split("\\")[:-1])

    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    df = pd.read_csv(csv_file)
    df['filename'] = df['filename'].apply(lambda x: os.path.join(audiomoth_folder, x))
    print(df['filename'][0])
    df['date'] = pd.to_datetime(df['date'])
    df['LA_median'] = df['LA'].rolling(window=WINDOW_SIZE, min_periods=1).quantile(0.5) + 10
    above_threshold = df[df['LA'] > df['LA_median']]

    if not above_threshold.empty:
        peaks, properties = find_peaks(above_threshold['LA'], prominence=PROMINENCE, width=WIDTH)
        df_peaks = above_threshold.iloc[peaks]
        print(f"Detected {len(df_peaks)} peaks")

        start_points = properties['left_ips']
        end_points = properties['right_ips']
        durations = end_points - start_points
        # round the durations to 2 decimal places
        durations = np.round(durations, 2)
        prominences = properties['prominences']
        prominences = np.round(prominences, 2)

        peaks_df = pd.DataFrame({
            # add filename 
            'filename': df_peaks['filename'].values,
            'start': above_threshold.iloc[start_points]['date'].values,
            'end': above_threshold.iloc[end_points]['date'].values,
            'duration': durations
        })
        print(peaks_df)

        mean = np.mean(durations)
        mean_rounded = np.round(mean, 2)
        print(f"\nAverage duration: {mean_rounded} seconds")
        print(f"Max duration: {np.max(durations)} seconds")
        print(f"Min duration: {np.min(durations)} seconds\n")

        # peaks_df.to_csv(os.path.join(output_folder, f"peaks_{title}_test.csv"), index=False)
        # print(f"Save the peaks to a csv file in {os.path.join(output_folder, f'peaks_{title}_test.csv')}")

        for idx, row in peaks_df.iterrows():
            extract_and_predict(row['filename'], row['start'], row['end'], row['duration'])

    else:
        print("No peaks detected")


if __name__ == "__main__":
    main()
