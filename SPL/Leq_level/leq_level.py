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
import logging
from utils import *

logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s', 
    filename='leq_level.log', 
    filemode='a'
    )



class LeqLevelOctave:
    def __init__(self, fs, calibration_constant, window_size):
        self.fs = fs
        self.C = calibration_constant
        self.window_size = window_size
        self.bA, self.aA = a_weighting_coeffs_design(fs)
        self.bC, self.aC = c_weighting_coeffs_design(fs)
        self.fast_samples = int(window_size / 8)
        logging.info(f"LeqLevelOctave initialized with fs: {fs}, C: {calibration_constant}, window_size: {window_size}")


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

            # getting the LC-LA difference
            LC_LA = LC - LA

            db_levels.append([LA, LC, LZ, LC_LA, Lmax, Lmin])
        return np.round(db_levels, 2)
    


def read_calibration_constants(ini_file):
    config = configparser.ConfigParser()
    config.read(ini_file)
    logging.info(f"Reading calibration constants from {ini_file}")
    return {key: float(value) for key, value in config['CalibrationConstants'].items()}



def get_device_id(metadata):
        artist_tags = metadata.tags.get("artist", ["songmeter"])
        if not artist_tags or len(artist_tags[0].split(" ")) < 2:
            return "songmeter"
        logging.info(f"Device ID: {artist_tags[0].split(' ')[1].lower()}")
        return artist_tags[0].split(" ")[1].lower()


def find_audiomoth_folders(base_path):
    for root, dirs, files in os.walk(base_path):
        if 'AUDIOMOTH' in dirs:
            yield root


def parse_arguments():
    parser = argparse.ArgumentParser(description='Calculate SPL levels for audio files in a directory')
    parser.add_argument('-p', '--path', type=str, required=True, help='Directory to be processed')
    return parser.parse_args()


def main():
    # python leq_level.py -p "\\192.168.205.117\AAC_Server\PUERTOS\NOISEPORT\20231211_SANTUR\"

    stable_version = get_stable_version()
    args = parse_arguments()
    base_path = args.path
    calibration_constants = read_calibration_constants('calibration_constants.ini')
    col_names = ['LA', 'LC', 'LZ', 'LC-LA', 'LAmax', 'LAmin', 'filename', 'date']

    audiomoth_folders = list(find_audiomoth_folders(base_path))
    for subfolder in tqdm(audiomoth_folders, desc='Processing folders'):
        logging.info(f"Processing audio files in: {subfolder}...")
        audio_path = os.path.join(subfolder, "AUDIOMOTH")
        if not os.path.exists(audio_path):
            logging.warning(f"Skipping {subfolder}, AUDIOMOTH folder not found.")
            continue
        audio_files = get_audiofiles(audio_path)
        if not audio_files:
            logging.warning(f"No audio files found in: {audio_path}")
            continue


        # read metadata
        sample_rates = []
        valid_audio_files = []
        logging.info(f"Reading metadata...")
        for file in tqdm(audio_files, desc='Reading metadata'):
            try:
                metadata = audio_metadata.load(os.path.join(audio_path, file))
                sample_rates.append(metadata.streaminfo.sample_rate)
                valid_audio_files.append(file)
            except Exception as e:
                logging.warning(f'Error reading file metadata: {file}, {e}')
        if not sample_rates:
            logging.warning("No valid audio files to process.")
            continue
        if not valid_audio_files:
            logging.warning(f"No valid audio files to process in {subfolder}")
            continue
        logging.info(f'Processing {len(valid_audio_files)} files in {subfolder}')

        fs_filterbanks = np.median(sample_rates)
        logging.info(f'Using sample rate: {fs_filterbanks}')
        
        
        # process audio files
        all_data_subfolder = []
        for audio_file in tqdm(valid_audio_files, desc='Processing audio files'):
            try:
                logging.info(f"Processsing file: {audio_file}...")
                filepath = os.path.join(audio_path, audio_file)
                metadata = audio_metadata.load(filepath)
                device_id = get_device_id(metadata)
                C = calibration_constants.get(device_id, -10.16)
                calculator = LeqLevelOctave(fs_filterbanks, C, int(fs_filterbanks))
                logging.info(f'Processing file: {audio_file} with calibration constant: {C} and sample rate: {fs_filterbanks} Hz')

                audio_data, _ = sf.read(filepath)
                db_levels = calculator.calculate_spl_levels(audio_data)

                if db_levels.shape[1] != 6:
                    logging.warning(f'Unexpected shape for db_levels: {db_levels.shape} for file {audio_file}')
                    continue

                name_split = audio_file.split(".")[0]
                start_timestamp = datetime.datetime.strptime(name_split, '%Y%m%d_%H%M%S')
                timestamps = [start_timestamp + datetime.timedelta(seconds=i) for i in range(db_levels.shape[0])]

                for row, timestamp in zip(db_levels, timestamps):
                    all_data_subfolder.append(list(row) + [audio_file, timestamp.strftime('%Y-%m-%d %H:%M:%S')])
            except Exception as e:
                logging.warning(f'Error processing file: {audio_file}, {e}')


        # save output to CSV
        if all_data_subfolder:
            df = pd.DataFrame(all_data_subfolder, columns=col_names)
            df = df.sort_values(by='date')

            subfolder = subfolder.split('\\')[-1]
            output_filename = f'leq_{subfolder}_{stable_version}.csv'
            output_folder = audio_path
            output_path = os.path.join(output_folder, output_filename)

            if not os.path.exists(output_folder):
                os.makedirs(output_folder)
                logging.info(f"Creating folder {output_folder}")
            else:
                logging.info(f"Folder {output_folder} already exists")
            
            df.to_csv(output_path, index=False)
            logging.info(f'Output saved to {output_path}')
        else:
            logging.warning(f"No data to save for folder {subfolder}")


if __name__ == '__main__':
    main()