import numpy as np
import pandas as pd
import soundfile as sf
from scipy.signal import lfilter
from pyfilterbank.splweighting import a_weighting_coeffs_design, c_weighting_coeffs_design
from tqdm import tqdm
from utils import *
import os
import datetime
import argparse
from scipy.signal import lfilter
import configparser
import audio_metadata
import logging

logging.basicConfig(filename='leq_levels.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class LeqLevelOct:
    def __init__(self, fs, calibration_constant, window_size, audio_path):
        self.fs = fs
        self.C = calibration_constant
        self.window_size = window_size
        self.audio_path = audio_path
        # A and C weighting filters
        self.bA, self.aA = a_weighting_coeffs_design(fs)
        self.bC, self.aC = c_weighting_coeffs_design(fs)
        # 1/3 and octave filter banks
        self.third_oct, self.octave = filterbanks(fs)

    def get_oct_levels(self, frame):
        y_oct, _ = self.third_oct.filter(frame)
        oct_level_temp = [get_db_level(y_band, self.C) for y_band in y_oct.T]
        return oct_level_temp

    def process_audio_files(self, audio_files):
        col_names = ['LA', 'LC', 'LZ', 'LAmax', 'LAmin']
        band_names = [f"{freq:.2f}Hz" for freq in self.third_oct.center_frequencies]
        col_names.extend(band_names)
        all_data = []

        for audio_file in audio_files:
            db = []
            x, _ = sf.read(os.path.join(self.audio_path, audio_file))
            
            name_split = audio_file.split(".")[0]
            start_timestamp = datetime.datetime.strptime(name_split, '%Y%m%d_%H%M%S')
            timestamps = [start_timestamp + datetime.timedelta(seconds=fstart/self.fs) for fstart in range(0, len(x) - self.window_size + 1, self.window_size)]
            
            # A and C weighting to the signal
            y_A_weighted = lfilter(self.bA, self.aA, x)
            y_C_weighted = lfilter(self.bC, self.aC, x)

            for fstart, timestamp in zip(range(0, len(x) - self.window_size + 1, self.window_size), timestamps):
                frame = x[fstart:fstart + self.window_size]
                yA = y_A_weighted[fstart:fstart + self.window_size]
                yC = y_C_weighted[fstart:fstart + self.window_size]

                # levels with weightings
                LA = round(get_db_level(yA, self.C), 2)
                LC = round(get_db_level(yC, self.C), 2)
                LZ = round(get_db_level(frame, self.C), 2)

                # LAmax and LAmin over fast intervals
                fast_levels = [get_db_level(yA[i:i + self.window_size // 8], self.C) for i in range(0, len(frame) - self.window_size // 8 + 1, self.window_size // 8)]
                Lmax = round(np.max(fast_levels), 2)
                Lmin = round(np.min(fast_levels), 2)
                
                # 1/3 levels
                oct_level_temp = [round(level, 2) for level in self.get_oct_levels(frame)]
                
                # lists 
                level_temp = [LA, LC, LZ, Lmax, Lmin] + oct_level_temp + [audio_file, timestamp.strftime('%Y-%m-%d-%H:%M:%S')]
                db.append(level_temp)
            all_data.append(db)
        return all_data
    

def read_calibration_constants(ini_file):
    config = configparser.ConfigParser()
    config.read(ini_file)
    return {key: float(value) for key, value in config['CalibrationConstants'].items()}

def get_device_id(metadata):
    artist_tags = metadata.tags.get("artist", ["songmeter"])
    if not artist_tags or len(artist_tags[0].split(" ")) < 2:
        return "songmeter"
    return artist_tags[0].split(" ")[1].lower()

def folder_result(path):
    result_folder = '5-Resultados'
    base_dir = os.path.dirname(os.path.dirname(path))
    result_path = os.path.join(base_dir, result_folder)
    if not os.path.exists(result_path):
        os.makedirs(result_path)
    return result_path

def parse_arguments():
    parser = argparse.ArgumentParser(description='Calculate SPL levels for audio files in a directory')
    parser.add_argument('-p', '--path', type=str, required=True, help='Directory to be processed')
    return parser.parse_args()


def main():
    args = parse_arguments()
    base_path = args.path
    calibration_constants = read_calibration_constants('calibration_constants.ini')
    result_folder = folder_result(base_path)

    for subfolder in tqdm(os.listdir(base_path), desc='Processing subfolders'):
        audio_path = os.path.join(base_path, subfolder, "AUDIOMOTH")
        if not os.path.exists(audio_path):
            logging.warning(f"Skipping {subfolder}, AUDIOMOTH folder not found.")
            continue

        audio_files = [file for file in os.listdir(audio_path) if file.lower().endswith('.wav')]
        if not audio_files:
            logging.warning(f"No audio files found in: {audio_path}")
            continue

        sample_rates = []
        valid_audio_files = []
        all_data_subfolder = []
        for file in audio_files:
            try:
                metadata = audio_metadata.load(os.path.join(audio_path, file))
                sample_rates.append(metadata.streaminfo.sample_rate)
                valid_audio_files.append(file)
            except Exception as e:
                logging.warning(f'Error reading file metadata: {file}, {e}')
        if not valid_audio_files:
            logging.warning(f"No valid audio files to process in {subfolder}")
            continue

        fs_filterbanks = np.median(sample_rates)
        calculator = LeqLevelOct(fs_filterbanks, -10.16, int(fs_filterbanks), audio_path)

        for audio_file in valid_audio_files:
            try:
                filepath = os.path.join(audio_path, audio_file)
                metadata = audio_metadata.load(filepath)
                device_id = get_device_id(metadata)
                C = calibration_constants.get(device_id, -10.16)
                calculator.C = C
                file_data = calculator.process_audio_files([audio_file])
                all_data_subfolder.extend(file_data)
            except Exception as e:
                logging.warning(f'Error processing file: {audio_file}, {e}')

        if all_data_subfolder:
            col_names = ['LA', 'LC', 'LZ', 'LAmax', 'LAmin'] + [f"{freq:.2f}Hz" for freq in calculator.third_oct.center_frequencies] + ['Filename', 'Time']
            flat_data = [item for sublist in all_data_subfolder for item in sublist]
            df_subfolder = pd.DataFrame(flat_data, columns=col_names)
            
            output_folder = os.path.join(result_folder, subfolder, 'SPL')
            if not os.path.exists(output_folder):
                os.makedirs(output_folder)

            output_filename = f'leq_levels_oct_{subfolder}.csv'
            output_path = os.path.join(output_folder, output_filename)
            df_subfolder.to_csv(output_path, index=False)
            logging.info(f'Output saved to {output_path}')
        else:
            logging.warning(f"No valid audio files to process in {subfolder}")

if __name__ == '__main__':
    main()