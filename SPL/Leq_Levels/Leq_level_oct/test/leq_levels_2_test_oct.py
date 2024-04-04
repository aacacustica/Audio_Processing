import numpy as np
import pandas as pd
import soundfile as sf
from scipy.signal import lfilter
from pyfilterbank.splweighting import a_weighting_coeffs_design, c_weighting_coeffs_design
from pyfilterbank.octbank import frequencies_fractional_octaves
from tqdm import tqdm
from utils import *
import os
import datetime
import argparse
from scipy.signal import lfilter, sosfilt
import configparser
import audio_metadata

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
                LA = get_db_level(yA, self.C)
                LC = get_db_level(yC, self.C)
                LZ = get_db_level(frame, self.C)
                # LAmax and LAmin over fast intervals
                fast_levels = [get_db_level(yA[i:i + self.window_size // 8], self.C) for i in range(0, len(frame) - self.window_size // 8 + 1, self.window_size // 8)]
                Lmax = np.max(fast_levels)
                Lmin = np.min(fast_levels)
                # 1/3 levels
                oct_level_temp = self.get_oct_levels(frame)
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
    parser.add_argument('--abrev', type=str, help='Abbreviation to identify the generated outputs')
    return parser.parse_args()




def main():
    args = parse_arguments()
    audio_path = args.path
    abrev = args.abrev if args.abrev else os.path.basename(audio_path)
    calibration_constants = read_calibration_constants('calibration_constants.ini')
    result_folder = folder_result(audio_path)

    assert os.path.exists(audio_path), f"Directory does not exist: {audio_path}"
    audio_files = [file for file in os.listdir(audio_path) if file.lower().endswith('.wav')]
    assert audio_files, "No audio files found in the directory"

    sample_rates = []
    valid_audio_files = []
    for file in audio_files:
        try:
            metadata = sf.info(os.path.join(audio_path, file))
            sample_rates.append(metadata.samplerate)
            valid_audio_files.append(file)
        except Exception as e:
            print(f'Error reading file metadata: {file}, {e}')
    if not sample_rates:
        print("No valid audio files to process.")
        return

    fs_filterbanks = np.median(sample_rates)
    # print(f'Median sample rate determined: {fs_filterbanks} Hz')

    calculator = LeqLevelOct(fs_filterbanks, -10.16, int(fs_filterbanks), audio_path)
    all_data = []
    for audio_file in tqdm(valid_audio_files, desc="Processing audio files"):
        filepath = os.path.join(audio_path, audio_file)
        metadata = audio_metadata.load(filepath)
        device_id = get_device_id(metadata)
        C = calibration_constants.get(device_id, -10.16)
        print(f'Processing file: {audio_file}, device_id: {device_id}, calibration constant: {C}')
        calculator.C = C  
        file_data = calculator.process_audio_files([audio_file])
        all_data.extend(file_data)

    col_names = ['LA', 'LC', 'LZ', 'LAmax', 'LAmin'] + [f"{freq:.2f}Hz" for freq in calculator.third_oct.center_frequencies] + ['Filename', 'Time']
    flat_data = [item for sublist in all_data for item in sublist]
    final_df = pd.DataFrame(flat_data, columns=col_names)
    
    final_df.to_csv(f'leq_levels_{abrev}_oct.csv', index=False)
    print(f'Output saved to leq_levels_{abrev}_oct.csv')

if __name__ == '__main__':
    main()