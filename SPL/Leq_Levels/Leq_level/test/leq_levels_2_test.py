import pandas as pd
import soundfile as sf
from scipy.signal import lfilter
import numpy as np
from pyfilterbank.splweighting import a_weighting_coeffs_design, c_weighting_coeffs_design
from utils import get_db_level
import argparse
import os
import datetime
from tqdm import tqdm
import configparser
import audio_metadata

class LeqLevel:
    def __init__(self, fs, calibration_constant, window_size):
        self.fs = fs
        self.C = calibration_constant
        self.window_size = window_size
        self.bA, self.aA = a_weighting_coeffs_design(fs)
        self.bC, self.aC = c_weighting_coeffs_design(fs)
        self.fast_samples = int(window_size / 8)

    def calculate_spl_levels(self, audio_data):
        db_levels = []
        for fstart in range(0, len(audio_data) - self.window_size + 1, self.window_size):
            frame = audio_data[fstart:fstart + self.window_size]
            yA = lfilter(self.bA, self.aA, frame)
            yC = lfilter(self.bC, self.aC, frame)

            LA = get_db_level(yA, self.C)
            LC = get_db_level(yC, self.C)
            LZ = get_db_level(frame, self.C)

            fast_levels = [get_db_level(yA[idx:idx + self.fast_samples], self.C)
                           for idx in range(0, len(frame) - self.fast_samples + 1, self.fast_samples)]
            Lmax = np.max(fast_levels)
            Lmin = np.min(fast_levels)

            db_levels.append([LA, LC, LZ, Lmax, Lmin])
        return np.round(db_levels, 2)
    

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
    result_folder = '\\5-Resultados'
    path = path.split('\\')[2:-2]
    path = '\\\\' + '\\'.join(path)
    if not os.path.exists(path):
        print(f"Skipping {path}, AUDIOMOTH folder not found.")
        return False
    else:
        if not os.path.exists(path + result_folder):
            os.makedirs(path + result_folder)
        else:
            result_folder = path + result_folder
    return result_folder

def parse_arguments():
    parser = argparse.ArgumentParser(description='Calculate SPL levels for audio files in a directory')
    parser.add_argument('-p', '--path', type=str, required=True, help='Directory to be processed')
    return parser.parse_args()


def main():
    args = parse_arguments()
    base_path = args.path
    calibration_constants = read_calibration_constants('calibration_constants.ini')
    col_names = ['LA', 'LC', 'LZ', 'LAmax', 'LAmin', 'Filename', 'Time']
    result_folder = folder_result(base_path)

    for subfolder in tqdm(os.listdir(base_path), desc='Processing subfolders'):
        audio_path = os.path.join(base_path, subfolder, "AUDIOMOTH")
        
        if not os.path.exists(audio_path):
            print(f"Skipping {subfolder}, AUDIOMOTH folder not found.")
            continue

        audio_files = [file for file in os.listdir(audio_path) if file.lower().endswith('.wav')]
        if not audio_files:
            print(f"No audio files found in: {audio_path}")
            continue

        sample_rates = []
        valid_audio_files = []
        for file in audio_files:
            try:
                metadata = audio_metadata.load(os.path.join(audio_path, file))
                sample_rates.append(metadata.streaminfo.sample_rate)
                valid_audio_files.append(file)
            except Exception as e:
                print(f'Error reading file metadata: {file}, {e}')
        if not sample_rates:
            print("No valid audio files to process.")
            continue
        if not valid_audio_files:
            print(f"No valid audio files to process in {subfolder}")
            continue

        fs_filterbanks = np.median(sample_rates)
        all_data_subfolder = []

        for audio_file in valid_audio_files:
            try:
                filepath = os.path.join(audio_path, audio_file)
                metadata = audio_metadata.load(filepath)
                device_id = get_device_id(metadata)
                C = calibration_constants.get(device_id, -10.16)
                calculator = LeqLevel(fs_filterbanks, C, int(fs_filterbanks))

                audio_data, _ = sf.read(filepath)
                db_levels = calculator.calculate_spl_levels(audio_data)

                if db_levels.shape[1] != 5:
                    print(f'Unexpected shape for db_levels: {db_levels.shape} for file {audio_file}')
                    continue

                name_split = audio_file.split(".")[0]
                start_timestamp = datetime.datetime.strptime(name_split, '%Y%m%d_%H%M%S')
                timestamps = [start_timestamp + datetime.timedelta(seconds=i) for i in range(db_levels.shape[0])]

                for row, timestamp in zip(db_levels, timestamps):
                    all_data_subfolder.append(list(row) + [audio_file, timestamp.strftime('%Y-%m-%d_%H:%M:%S')])
            except Exception as e:
                print(f'Error processing file: {audio_file}, {e}')

        if all_data_subfolder:
            df_subfolder = pd.DataFrame(all_data_subfolder, columns=col_names)
            output_filename = f'leq_levels_{subfolder}.csv'
            output_folder = os.path.join(result_folder, subfolder, 'SPL')
            output_path = os.path.join(output_folder, output_filename)
            df_subfolder.to_csv(output_path, index=False)
            print(f'Output saved to {output_path}')
        else:
            print(f"No data to save for folder {subfolder}")

if __name__ == '__main__':
    main()