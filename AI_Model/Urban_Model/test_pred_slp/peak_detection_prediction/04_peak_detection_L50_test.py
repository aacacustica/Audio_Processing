import pandas as pd
import matplotlib.pyplot as plt
from scipy.signal import find_peaks
import os
from datetime import datetime
from pydub import AudioSegment
from tqdm import tqdm
import numpy as np
import soundfile as sf

import params as yamnet_params
import yamnet as yamnet_model
import soundfile as sf
import resampy
import warnings


# warning messages disabled
warnings.filterwarnings("ignore", category=RuntimeWarning, message="Couldn't find ffmpeg or avconv")
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

WINDOW_SIZE = 30  # seconds
PROMINENCE = 1
WIDTH = 1
CLIP_DURATION = 3  # seconds



def extract_audio_clips(df, output_folder, clip_duration_sec):
    output_folder = os.path.join(output_folder, "peak_clips")
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    clips_num = 0
    first_5_rows = df.head(5)
    for index, row in tqdm(first_5_rows.iterrows(), total=first_5_rows.shape[0], desc="Extracting clips"):
        peak_date = row['date']
        filename = row['filename']
        start_time_str = os.path.basename(filename).split('.')[0]
        start_time = datetime.strptime(start_time_str, "%Y%m%d_%H%M%S")

        # take the offset in milliseconds which is the difference between the peak date and the start time
        peak_offset_ms = int((peak_date - pd.Timestamp(start_time)).total_seconds() * 1000)
        start_extract_ms = max(0, peak_offset_ms - int(clip_duration_sec * 1000 / 2))
        end_extract_ms = start_extract_ms + int(clip_duration_sec * 1000)

        # extract the audio clip
        audio = AudioSegment.from_file(filename)
        clip = audio[start_extract_ms:end_extract_ms]

        # convertion audiosegment to np-array
        samples = np.array(clip.get_array_of_samples())
        if clip.channels == 2:
            samples = samples.reshape((-1, 2))
        elif clip.channels == 1:
            samples = np.expand_dims(samples, axis=1)
        else:
            print(f"Clip {clip_name} has {clip.channels} channels. Skipping")
            continue

        # np array to a wav
        clip_name = f"clip_{peak_date.strftime('%Y%m%d_%H%M%S')}.wav"
        clip_path = os.path.join(output_folder, clip_name)
        sf.write(clip_path, samples, clip.frame_rate)

        # make predictions and update clip name
        classes, probabilities = make_clip_predictions(clip_path, clip_name)
        new_clip_name = f"clip_{peak_date.strftime('%Y%m%d_%H%M%S')}_{classes[0]}.wav"
        new_clip_path = os.path.join(output_folder, new_clip_name)
        
        # check if new_clip_path exists
        if os.path.exists(new_clip_path):
            print(f"Clip {new_clip_name} already exists. Skipping...")
            os.remove(clip_path)  # Remove the initially saved clip if the new name already exists
            continue
        
        # rename to include the class
        os.rename(clip_path, new_clip_path)

        print(f"[{clips_num}] Extracted clip saved to {new_clip_name} in {output_folder}")
        clips_num += 1
    print(f"Extracted {clips_num} clips")




def make_clip_predictions(clip, clip_name):
    params = yamnet_params.Params()
    yamnet = yamnet_model.yamnet_frames_model(params)
    yamnet.load_weights('yamnet.h5')
    yamnet_classes = yamnet_model.class_names('yamnet_class_map.csv')

    wav_data, sr = sf.read(clip, dtype=np.int16)
    print(f"Sample rate: {sr}")
    assert wav_data.dtype == np.int16, 'Bad sample type: %r' % wav_data.dtype
    waveform = wav_data / 32768.0  # Convert to [-1.0, +1.0]
    waveform = waveform.astype('float32')

    # Convert to mono and the sample rate expected by YAMNet.
    if len(waveform.shape) > 1:
      waveform = np.mean(waveform, axis=1)
    if sr != params.sample_rate:
      waveform = resampy.resample(waveform, sr, params.sample_rate)

    # Predict YAMNet classes.
    scores, embeddings, spectrogram = yamnet(waveform)
    # Scores is a matrix of (time_frames, num_classes) classifier scores.
    # Average them along time to get an overall classifier output for the clip.
    prediction = np.mean(scores, axis=0)
    # Report the highest-scoring classes and their scores.
    top3_i = np.argsort(prediction)[::-1][:3]
    print(f"Top 3 classes: {top3_i}")
    # return the top 3 classes and their probabilities
    return [yamnet_classes[i] for i in top3_i], [prediction[i] for i in top3_i]



def plot_peak_detection(df, df_peaks):
    plt.figure(figsize=(25, 8))
    plt.plot(df['date'], df['LA'], label='LA values')
    plt.plot(df['date'], df['LA_median'], color='cyan', linestyle='-', linewidth=2, label=f'Dynamic Threshold ({WINDOW_SIZE} seconds)')
    plt.scatter(df_peaks['date'], df_peaks['LA'], color='red', s=10, label='Peaks')
    plt.legend()
    plt.xlim(df['date'].iloc[0], df['date'].iloc[-1])
    plt.title(f'Peak Detection in Environmental Noise Data')
    plt.xlabel('Time')
    plt.ylabel('LA (dB)')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()



def main():
    csv_file = r"\\192.168.205.117\AAC_Server\PUERTOS\NOISEPORT\20231211_SANTUR\5-Resultados\P1_CONTENEDORES\SPL\leq_levels_P1_CONTENEDORES_v1_1_test.csv"
    audiomoth_folder = csv_file.replace("5-Resultados", "3-Medidas").replace("SPL", "AUDIOMOTH")
    audiomoth_folder = "\\".join(audiomoth_folder.split("\\")[:-1])
    output_folder = "\\".join(csv_file.split("\\")[:-1])
    
    print(f"AudioMoth folder: {audiomoth_folder}")
    print(f"Output folder: {output_folder}")

    if not os.path.exists(output_folder):
        print("Creating folder")
        os.makedirs(output_folder)
    else:
        print("Folder already exists")

    df = pd.read_csv(csv_file)
    df['filename'] = df['filename'].apply(lambda x: os.path.join(audiomoth_folder, x))
    df['date'] = pd.to_datetime(df['date'])
    df['LA_median'] = df['LA'].rolling(window=WINDOW_SIZE, min_periods=1).quantile(0.5) + 10
    above_threshold = df[df['LA'] > df['LA_median']]

    if not above_threshold.empty:
        peaks, _ = find_peaks(above_threshold['LA'], prominence=PROMINENCE, width=WIDTH)
        df_peaks = above_threshold.iloc[peaks]
        print(f"Detected {len(df_peaks)} peaks")
        extract_audio_clips(df_peaks, output_folder, CLIP_DURATION)
    else:
        print("No peaks detected")

    plot_peak_detection(df, df_peaks)


if __name__ == "__main__":
    main()