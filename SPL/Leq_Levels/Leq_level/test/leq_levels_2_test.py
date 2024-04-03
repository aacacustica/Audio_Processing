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
import logging

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
    
def parse_arguments():
    parser = argparse.ArgumentParser(description='Calculate SPL levels for audio files in a directory')
    parser.add_argument('-p', '--path', type=str, required=True, help='Directory to be processed')
    parser.add_argument('--abrev', type=str, help='Abbreviation to identify the generated outputs')
    return parser.parse_args()

def main():
    args = parse_arguments()
    audio_path = args.path
    abrev = args.abrev if args.abrev else os.path.basename(audio_path)

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
            logging.error(f'Error reading file metadata: {file}, {e}')

    if not valid_audio_files:
        print("No valid audio files to process.")
        return

    fs_filterbanks = np.median(sample_rates)
    print(f'Median sample rate determined: {fs_filterbanks} Hz')

    C = -14.08  # default calibration constant
    calculator = LeqLevel(fs_filterbanks, C, int(fs_filterbanks))
    col_names = ['LA', 'LC', 'LZ', 'LAmax', 'LAmin', 'Filename', 'Timestamp']
    all_data = []

    for audio_file in tqdm(valid_audio_files, desc="Processing audio files"):
        try:
            filepath = os.path.join(audio_path, audio_file)
            audio_data, _ = sf.read(filepath)
            db_levels = calculator.calculate_spl_levels(audio_data)

            if db_levels.shape[1] != 5:
                logging.error(f'Unexpected shape for db_levels: {db_levels.shape} for file {audio_file}')
                continue

            name_split = audio_file.split(".")[0]
            start_timestamp = datetime.datetime.strptime(name_split, '%Y%m%d_%H%M%S')
            timestamps = [start_timestamp + datetime.timedelta(seconds=i) for i in range(db_levels.shape[0])]

            for row, timestamp in zip(db_levels, timestamps):
                all_data.append(list(row) + [audio_file, timestamp.strftime('%Y-%m-%d_%H:%M:%S')])
        except Exception as e:
            logging.error(f'Error processing file: {audio_file}, {e}')

    # save output to csv
    df = pd.DataFrame(all_data, columns=col_names)
    df.to_csv(f'leq_levels_{abrev}.csv', index=False)
    print(f'Output saved to leq_levels_{abrev}.csv')

if __name__ == '__main__':
    main()