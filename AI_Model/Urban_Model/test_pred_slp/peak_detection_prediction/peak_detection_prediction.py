import pandas as pd
import numpy as np
from scipy.signal import find_peaks
import os
from pydub import AudioSegment
import matplotlib.pyplot as plt

from utils import *
import logging

import tensorflow as tf
import warnings


# warning messages disabled
warnings.filterwarnings("ignore", category=RuntimeWarning, message="Couldn't find ffmpeg or avconv")
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s', 
    filename='peak_detection_prediction.log', 
    filemode='a'
    )

# memory growth for GPU for each device
gpus = tf.config.experimental.list_physical_devices('GPU')
if gpus:
    try:
        for gpu in gpus:
            tf.config.experimental.set_memory_growth(gpu, True)
            logical_gpus = tf.config.experimental.list_logical_devices('GPU')
            print(f"{len(gpus)} Physical GPUs, {len(logical_gpus)} Logical GPUs")
    except RuntimeError as e:
        print(e)



def main():
    # open csv file
    logging.info("Opening csv file")
    csv_file = r"\\192.168.205.117\AAC_Server\PUERTOS\NOISEPORT\20231211_SANTUR\5-Resultados\P1_CONTENEDORES\SPL\leq_levels_P1_CONTENEDORES_v1_1_test.csv"
    df = pd.read_csv(csv_file)
    title = csv_file.split("\\")[-3]

    logging.info(f"Handling csv file")
    # get the audiomoth folder
    audiomoth_folder = csv_file.replace("5-Resultados", "3-Medidas").replace("SPL", "AUDIOMOTH")
    # remove last item from audio moth folder
    audiomoth_folder = "\\".join(audiomoth_folder.split("\\")[:-1])

    output_folder = "\\".join(csv_file.split("\\")[:-1])
    logging.info(f"Output folder: {output_folder}")

    if not os.path.exists(output_folder):
        logging.info("Creating folder")
    else:
        logging.info("Folder already exists")

    # change the filename to the full path
    df['filename'] = df['filename'].apply(lambda x: os.path.join(audiomoth_folder, x))
    # convert date column to datetime
    df['date'] = pd.to_datetime(df['date'])

    duration = (df['date'].iloc[-1] - df['date'].iloc[0]).total_seconds()
    logging.info(f"Duration: {duration} seconds, {duration/60} minutes, {duration/3600} hours, {duration/3600/24} days")



    logging.info("Calculating the median")
    df['LA_median'] = df['LA'].rolling(window=WINDOW_SIZE, min_periods=1).quantile(0.5) + 10
    # dynamic threshold by filtering data points
    above_threshold = df[df['LA'] > df['LA_median']]
    

    # find peaks in the filtered data
    if not above_threshold.empty:
        peaks, properties = find_peaks(above_threshold['LA'], prominence=PROMINENCE, width=WIDTH)
        peak_filenames = above_threshold.iloc[peaks]['filename'].values
        start_times = np.round(properties['left_ips'], 2)
        end_times = np.round(properties['right_ips'], 2)
        duration = np.round(end_times - start_times, 2)
        
        # df for each peak
        peaks_df = pd.DataFrame({
            'filename': peak_filenames,
            'start_time': start_times,
            'end_time': end_times,
            'duration': duration
        })
        
        # save csv file
        # peaks_df.to_csv(os.path.join(output_folder, f"peaks_raw_{title}.csv"), index=False)

        print(peaks_df)

        # print the average of the duration
        print(f"Average duration: {np.mean(duration)} seconds")
        print(f"Max duration: {np.max(duration)} seconds")
        print(f"Min duration: {np.min(duration)} seconds")

        # Create the histogram
        plt.hist(duration, bins=50)

        # Set labels and title
        plt.xlabel("Duration (seconds)")
        plt.ylabel("Frequency")
        plt.title("Duration of peaks")

        # Set zoomed-in limits for x and y axes (example values)
        plt.xlim(0, 50)  # Adjust these values to zoom in on the desired range
        plt.ylim(0, 50)   # Adjust these values to zoom in on the desired range

        # Show the plot
        plt.show()

        exit()

        # take the sr from the first audio file
        if len(peak_filenames) > 0:
            audio_file = peak_filenames[0]
            audio = AudioSegment.from_file(audio_file)
            sampling_rate = audio.frame_rate
            
            # SAVING CLIPS FROM PEAKS
            save_clips_from_peaks(peaks_df, output_folder, sampling_rate, title, logging)



if __name__ == "__main__":
    main()