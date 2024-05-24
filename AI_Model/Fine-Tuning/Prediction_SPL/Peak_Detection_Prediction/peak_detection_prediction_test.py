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


    WINDOW_SIZE = 5
    PROMINENCE = 1
    WIDTH = 1
    
def main():
    # Open csv file
    logging.info("Opening csv file")
    csv_file = r"\\192.168.205.117\AAC_Server\PUERTOS\NOISEPORT\20231211_SANTUR\5-Resultados\P1_CONTENEDORES\SPL\leq_levels_P1_CONTENEDORES_v1_1_test.csv"
    df = pd.read_csv(csv_file)
    title = csv_file.split("\\")[-3]

    logging.info(f"Handling csv file")
    audiomoth_folder = csv_file.replace("5-Resultados", "3-Medidas").replace("SPL", "AUDIOMOTH")
    audiomoth_folder = "\\".join(audiomoth_folder.split("\\")[:-1])
    output_folder = "\\".join(csv_file.split("\\")[:-1])
    logging.info(f"Output folder: {output_folder}")

    df['filename'] = df['filename'].apply(lambda x: os.path.join(audiomoth_folder, x))
    df['date'] = pd.to_datetime(df['date'])

    # processing each file separately
    peak_results = []
    for file_name in df['filename'].unique():
        file_data = df[df['filename'] == file_name].reset_index()
        file_data['LA_median'] = file_data['LA'].rolling(window=WINDOW_SIZE, min_periods=1).quantile(0.5) + 10
        above_threshold = file_data[file_data['LA'] > file_data['LA_median']]

        if not above_threshold.empty:
            peaks, properties = find_peaks(above_threshold['LA'], prominence=PROMINENCE, width=WIDTH)
            if peaks.size > 0:
                peak_df = pd.DataFrame({
                    'filename': file_name,
                    'start_time': np.round(properties['left_ips'], 2),
                    'end_time': np.round(properties['right_ips'], 2),
                    'duration': np.round(properties['right_ips'] - properties['left_ips'], 2)
                })
                peak_results.append(peak_df)

    if peak_results:
        peaks_df = pd.concat(peak_results)
        # peaks_df.to_csv(os.path.join(output_folder, f"peaks_raw_{title}.csv"), index=False)
        print(peaks_df)
        print(len(peaks_df))
    else:
        logging.info("No peaks detected")

if __name__ == "__main__":
    main()
