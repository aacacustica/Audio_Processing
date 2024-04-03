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
    def __init__(self, fs, window_size, audio_path, calibration_file='calibration_constants.ini'):
        self.fs = fs
        self.window_size = window_size
        self.audio_path = audio_path

        self.config = configparser.ConfigParser()
        self.config.read(calibration_file)
        self.calibration_dict = {k: float(v) for k, v in self.config['CalibrationConstants'].items()}

        # A and C weighting filters
        self.bA, self.aA = a_weighting_coeffs_design(fs)
        self.bC, self.aC = c_weighting_coeffs_design(fs)

        # Third-octave and octave filter banks
        self.third_oct, self.octave = filterbanks(fs)

    def get_oct_levels(self, frame):
        y_oct, _ = self.third_oct.filter(frame)
        oct_level_temp = [get_db_level(y_band, self.C) for y_band in y_oct.T]
        return oct_level_temp

    def process_audio_files(self, audio_files, C):
        col_names = ['LA', 'LC', 'LZ', 'LAmax', 'LAmin']
        band_names = [f"{freq:.2f}Hz" for freq in self.third_oct.center_frequencies]
        col_names.extend(band_names)
        all_data = []

        for audio_file in tqdm(audio_files, desc="Processing audio files"):
            db = []
            x, _ = sf.read(os.path.join(self.audio_path, audio_file))
            
            # Apply A and C weighting to the signal
            y_A_weighted = lfilter(self.bA, self.aA, x)
            y_C_weighted = lfilter(self.bC, self.aC, x)

            for fstart in range(0, len(x) - self.window_size + 1, self.window_size):
                frame = x[fstart:fstart + self.window_size]
                yA = y_A_weighted[fstart:fstart + self.window_size]
                yC = y_C_weighted[fstart:fstart + self.window_size]

                # Total levels with weightings
                LA = get_db_level(yA, self.C)
                LC = get_db_level(yC, self.C)
                LZ = get_db_level(frame, self.C)

                # Calculating LAmax and LAmin over fast intervals
                fast_levels = [get_db_level(yA[i:i + self.window_size // 8], self.C) for i in range(0, len(frame) - self.window_size // 8 + 1, self.window_size // 8)]
                Lmax = np.max(fast_levels)
                Lmin = np.min(fast_levels)

                # Third-octave levels in Z weighting
                oct_level_temp = self.get_oct_levels(frame)

                # Temporary lists creation
                level_temp = [LA, LC, LZ, Lmax, Lmin] + oct_level_temp
                db.append(level_temp)

            db = np.array(db)
            db = np.round(db, 2)
            name = audio_file.split(".")[0]
            timestamps = [datetime.datetime.strptime(name, '%Y%m%d_%H%M%S') + datetime.timedelta(seconds=i) for i in range(len(db))]
            file_data = pd.DataFrame(db, columns=col_names)
            file_data['Filename'] = audio_file
            file_data['Timestamp'] = timestamps
            all_data.append(file_data)

        return pd.concat(all_data, ignore_index=True)

def get_device_id(metadata):
        artist_tags = metadata.tags.get("artist", ["songmeter"])
        if not artist_tags or len(artist_tags[0].split(" ")) < 2:
            return "songmeter"
        return artist_tags[0].split(" ")[1].lower()

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
    for file in audio_files:
        try:
            metadata = sf.info(os.path.join(audio_path, file))
            sample_rates.append(metadata.samplerate)

            metadata_id = audio_metadata.load(os.path.join(audio_path, file))
            print(metadata_id)
            device_id = get_device_id(metadata_id)
            print(device_id)
            C = float(config['CalibrationConstants'][device_id])
            print(C)
        except Exception as e:
            print(f'Error reading file metadata: {file}, {e}')
    if not sample_rates:
        print("No valid audio files to process.")
        return

    fs_filterbanks = np.median(sample_rates)
    print(f'Median sample rate determined: {fs_filterbanks} Hz')

    calculator = LeqLevelOct(fs_filterbanks, C, int(fs_filterbanks), audio_path)
    df = calculator.process_audio_files(audio_files)
    
    # Save output to CSV
    df.to_csv(f'leq_levels_{abrev}_oct.csv', index=False)
    print(f'Output saved to leq_levels_{abrev}_oct.csv')

if __name__ == '__main__':
    main()