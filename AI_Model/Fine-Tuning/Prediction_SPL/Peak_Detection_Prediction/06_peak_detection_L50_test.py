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
import logging

from visualization import *
import argparse

import params as yamnet_params
import yamnet as yamnet_model

logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s', 
    filename='peak_detection.log', 
    filemode='a'
    )

# warning messages disabled
warnings.filterwarnings("ignore", category=RuntimeWarning, message="Couldn't find ffmpeg or avconv")
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

WINDOW_SIZE = 30  # seconds
PROMINENCE = 1
WIDTH = 1


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
    top3_i = np.argsort(prediction)[::-1][:2]
    # logging.info the na,e of the class
    logging.info(f"Top 3 classes: {[yamnet_classes[i] for i in top3_i]}")
    return [yamnet_classes[i] for i in top3_i], [prediction[i] for i in top3_i]


def argument_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv_file", type=str, required=False, help="Path to the csv file")
    return parser.parse_args()


def main():
    args = argument_parser()
    if args.csv_file:
        csv_file = args.csv_file
    else:
        csv_file = r"\\192.168.205.117\AAC_Server\PUERTOS\NOISEPORT\20231211_SANTUR\3-Medidas\P1_CONTENEDORES\AUDIOMOTH\leq_P1_CONTENEDORES_v2_0.csv"
    df = pd.read_csv(csv_file)
    

    title = csv_file.split("\\")[-3]
    audiomoth_folder = csv_file.replace("5-Resultados", "3-Medidas").replace("SPL", "AUDIOMOTH")
    audiomoth_folder = "\\".join(audiomoth_folder.split("\\")[:-1])
    output_folder = "\\".join(csv_file.split("\\")[:-1])
    output_folder = output_folder.replace("3-Medidas", "5-Resultados").replace("AUDIOMOTH", "SPL")

    if not os.path.exists(output_folder):
        os.makedirs(output_folder)


    ############# PLOT THE DATA #############
    # plot the LA values
    # plot_LA(df)
    # plot_LA_night(df)
    # plot_global_values(df)
    # plot_some_values(df)

    df['filename'] = df['filename'].apply(lambda x: os.path.join(audiomoth_folder, x))
    df['date'] = pd.to_datetime(df['date'])
    df['LA_median'] = df['LA'].rolling(window=WINDOW_SIZE, min_periods=1).quantile(0.5) + 10
    above_threshold = df[df['LA'] > df['LA_median']]


    if not above_threshold.empty:
        clip_info = []
        peaks, properties = find_peaks(above_threshold['LA'], prominence=PROMINENCE, width=WIDTH)
        df_peaks = above_threshold.iloc[peaks]
        logging.info(f"Detected {len(df_peaks)} peaks")

        start_points = properties['left_ips']
        end_points = properties['right_ips']
        durations = end_points - start_points
        # round the durations to 2 decimal places
        durations = np.round(durations, 2)
        prominences = properties['prominences']
        prominences = np.round(prominences, 2)

        peaks_df = pd.DataFrame({
            'filename': df_peaks['filename'].values,
            'start': above_threshold.iloc[start_points]['date'].values,
            'end': above_threshold.iloc[end_points]['date'].values,
            'duration': durations
        })


        mean = np.mean(durations)
        mean_rounded = np.round(mean, 2)
        logging.info("")
        logging.info(f"Average duration: {mean_rounded} seconds")
        logging.info(f"Max duration: {np.max(durations)} seconds")
        logging.info(f"Min duration: {np.min(durations)} seconds\n")
        
        num_peaks_processed = 0
        # uncomment the line below to process only the first 50 peaks
        # peaks_df = peaks_df.head(50)
        # adding a tqdm progress bar
        for index, row in tqdm(peaks_df.iterrows(), total=len(peaks_df)):
            logging.info(f"\nExtracting segment from {row['filename']}\n")
            try:
                # Read the entire audio file
                wav_data, sr = sf.read(row['filename'], dtype=np.int16)
                logging.info(f"Sample rate: {sr}")
            except Exception as e:
                logging.warning(f"Failed to read file {row['filename']}. Error: {e}")
                return None
            
            # start time of the audio file
            start_time_audio = row['filename']
            start_time_audio = start_time_audio.split('\\')[-1].split('_')
            start_time_audio = start_time_audio[0] + start_time_audio[1].split('.')[0]
            start_time_audio = datetime.strptime(start_time_audio, '%Y%m%d%H%M%S')
            logging.info(f"Start time of the audio file: {start_time_audio}")


            # get start and end time of the peak
            start_time = row['start']
            end_time = row['end']
            duration = row['duration']
            logging.info(f"Start time: {start_time}, End time: {end_time}, Duration: {duration}")

            ##### SLICE AUDIO #####
            start_time = (row['start'] - pd.Timestamp(start_time_audio)).total_seconds()
            end_time = (row['end'] - pd.Timestamp(start_time_audio)).total_seconds()

            # samples indices, add a secondto the start and the end time
            start_index = int((start_time - 0.25) * sr)
            end_index = int((end_time + 0.25) * sr)

            # extract segment
            segment = wav_data[start_index:end_index]
            actual_segment_duration = len(segment) / sr
            # if actual_segment_duration == 0, skip the peak and the segment
            if actual_segment_duration == 0:
                logging.warning(f"Segment duration {actual_segment_duration}")
                logging.warning("Segment duration is 0, skipping the peak, it beloong to two different audio files\n\n")
                continue
            elif actual_segment_duration > duration + 20:
                logging.warning(f"Segment duration {actual_segment_duration}")
                logging.warning("Segment duration is more than 10s, skipping the peak, it beloong to two different audio files\n\n")
                continue                
            else:
                logging.info(f"Actual Segment duration: {actual_segment_duration} seconds\n\n")
            

            # START PREDICTION
            wave_form = segment / 32768.0  # Convert to [-1.0, +1.0]
            wave_form = wave_form.astype('float32')
            
            # make predictions
            classes, predictions = make_clip_predictions(wave_form, sr)
            num_peaks_processed += 1


            #### MAKE A CLIP AND SAVE IT ####
            peak_date_str = row['start'].strftime('%Y%m%d_%H%M%S')
            clip_filename = f"{peak_date_str}_{classes[0]}.wav"
            logging.info(f"Clip filename: {clip_filename}")
            os.makedirs(os.path.join(output_folder, 'peak_clips'), exist_ok=True)
            clip_path = os.path.join(output_folder, 'peak_clips', clip_filename)
            sf.write(clip_path, segment, sr)
            logging.info(f"Segment {clip_filename} saved to {clip_path}")


            #### SAVE INFO IN A CSV ####
            clip_info.append({
                'filename': clip_path,
                'start_time': row['start'],
                'end_time': row['end'],
                'duration': actual_segment_duration,
                'classes': classes,
                'predictions': predictions
            })
            logging.info(f"Clip info: \n{clip_info[-1]}")


        # save the info in a csv
        clips_df = pd.DataFrame(clip_info)
        # save the csv into the peak_clips folder
        clips_df.to_csv(os.path.join(output_folder, 'peak_clips', f"{title}_peak_clips.csv"), index=False)
        logging.info(f"Extracted {num_peaks_processed} clips and saved information at {output_folder}")
        logging.info(f"Actual Processed {num_peaks_processed} peaks")
    
    else:
        logging.error("No peaks detected")



if __name__ == "__main__":
    main()