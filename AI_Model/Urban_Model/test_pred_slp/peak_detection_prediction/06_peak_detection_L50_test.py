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
    # print the na,e of the class
    print(f"Top 3 classes: {[yamnet_classes[i] for i in top3_i]}")
    return [yamnet_classes[i] for i in top3_i], [prediction[i] for i in top3_i]



def extract_and_predict(filename, start_time, end_time, expected_duration):
    print(f"Extracting segment from {filename}\n")
    try:
        # Read the entire audio file
        wav_data, sr = sf.read(filename, dtype=np.int16)
    except Exception as e:
        print(f"Failed to read file {filename}. Error: {e}")
        return None

    # Parse recording start time from filename
    datetime_string = filename.split('\\')[-1].split('_')
    date_part, time_part = datetime_string[0], datetime_string[1].split('.')[0]
    recording_start_time = datetime.strptime(date_part + time_part, '%Y%m%d%H%M%S')
    print(f"Recording start time: {recording_start_time}")

    # Compute start and end times in seconds relative to the file start
    start_seconds = (start_time - recording_start_time).total_seconds()
    end_seconds = (end_time - recording_start_time).total_seconds()

    # Calculate start and end indices for the audio data
    start_index = int(start_seconds * sr)
    end_index = int(math.ceil(end_seconds * sr))

    # Ensure the indices are within the bounds of the data
    if start_index < 0 or end_index <= start_index or end_index > len(wav_data):
        print(f"Invalid indices or out of bounds. Start index: {start_index}, End index: {end_index}")
        return None

    # Extract the segment
    segment = wav_data[start_index:end_index]
    actual_segment_duration = len(segment) / sr

    # Log details about the extraction
    print(f"File sample rate: {sr}, Total samples: {len(wav_data)}")
    print(f"Start index: {start_index}, End index: {end_index}")
    print(f"Start seconds: {start_seconds}, End seconds: {end_seconds}")
    print(f"Segment duration: {end_seconds - start_seconds} seconds")
    print(f"Actual Duration from DF: {expected_duration} seconds")
    print(f"Actual Segment duration: {actual_segment_duration} seconds\n\n")

    # Convert segment to normalized float32
    wave_form = segment / 32768.0  # Convert to [-1.0, +1.0]
    wave_form = wave_form.astype('float32')


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
        # print(peaks_df)

        mean = np.mean(durations)
        mean_rounded = np.round(mean, 2)
        print(f"\nAverage duration: {mean_rounded} seconds")
        print(f"Max duration: {np.max(durations)} seconds")
        print(f"Min duration: {np.min(durations)} seconds\n")
        

        num_peaks_processed = 0
        peaks_df = peaks_df.head(50)
        for idx, row in peaks_df.iterrows():
            print(f"\nExtracting segment from {row['filename']}\n")
            try:
                # Read the entire audio file
                wav_data, sr = sf.read(row['filename'], dtype=np.int16)
                print(f"Sample rate: {sr}")
            except Exception as e:
                print(f"Failed to read file {row['filename']}. Error: {e}")
                return None
            
            # start time of the audio file
            start_time_audio = row['filename']
            start_time_audio = start_time_audio.split('\\')[-1].split('_')
            start_time_audio = start_time_audio[0] + start_time_audio[1].split('.')[0]
            start_time_audio = datetime.strptime(start_time_audio, '%Y%m%d%H%M%S')
            print(f"Start time of the audio file: {start_time_audio}")


            # get start and end time of the peak
            start_time = row['start']
            end_time = row['end']
            duration = row['duration']
            print(f"Start time: {start_time}, End time: {end_time}, Duration: {duration}")

            ##### SLICE AUDIO #####
            start_time = (row['start'] - pd.Timestamp(start_time_audio)).total_seconds()
            end_time = (row['end'] - pd.Timestamp(start_time_audio)).total_seconds()

            # samples indices, add a secondto the start and the end time
            start_index = int((start_time - 0.25) * sr)
            end_index = int((end_time + 0.25) * sr)
            # start_index = int((start_time) * sr)
            # end_index = int((end_time) * sr)

            # extract segment
            segment = wav_data[start_index:end_index]
            actual_segment_duration = len(segment) / sr
            # if actual_segment_duration == 0, skip the peak and the segment
            if actual_segment_duration == 0:
                print(f"Segment duration {actual_segment_duration}")
                print("Segment duration is 0, skipping the peak, it beloong to two different audio files\n\n")
                continue
            elif actual_segment_duration > duration + 20:
                print(f"Segment duration {actual_segment_duration}")
                print("Segment duration is more than 10s, skipping the peak, it beloong to two different audio files\n\n")
                continue                
            else:
                print(f"Actual Segment duration: {actual_segment_duration} seconds\n\n")
            
            # START PREDICTION
            wave_form = segment / 32768.0  # Convert to [-1.0, +1.0]
            wave_form = wave_form.astype('float32')
            
            # make predictions
            make_clip_predictions(wave_form, sr)
            num_peaks_processed += 1

        print(f"Actual Processed {num_peaks_processed} peaks")
    
    else:
        print("No peaks detected")

if __name__ == "__main__":
    main()