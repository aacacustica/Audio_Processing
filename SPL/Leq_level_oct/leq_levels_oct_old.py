import numpy as np
import pandas as pd
import soundfile as sf

# from scipy.signal import lfilter
from lfilter_numpy import lfilter_np
from pyfilterbank.splweighting import a_weighting_coeffs_design, c_weighting_coeffs_design
from utils import *


from tqdm import tqdm
import os
import datetime
import argparse
import configparser
import audio_metadata
import logging


logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s', 
    filename='leq_level_1_3_oct.log', 
    filemode='w'
    )



class LeqLevelOct:
    def __init__(self, fs, calibration_constant, window_size, audio_path):
        """
        Set up the LeqLevelOct object with the necessary parameters
        :param fs:
            Sample rate of the audio
        :param calibration_constant:
            Calibration constant for the microphone
        :param window_size:
            Size of the window for calculating SPL levels
        :param audio_path:
            Path to the audio files
        """
        self.fs = fs
        self.C = calibration_constant
        self.window_size = window_size
        self.audio_path = audio_path
        # A and C weighting filters
        self.bA, self.aA = a_weighting_coeffs_design(fs)
        self.bC, self.aC = c_weighting_coeffs_design(fs)
        # 1/3 and octave filter banks
        self.third_oct, self.octave = filterbanks(fs)
        logging.info(f"LeqLevelOct initialized with fs: {fs}, C: {calibration_constant}, window_size: {window_size}")



    def get_oct_levels(self, frame):
        """Calculate 1/3 octave levels for a frame of audio data
        :param frame:
            Frame of audio data
        :return:
            List of 1/3 octave levels
        """
        y_oct, _ = self.third_oct.filter(frame)
        oct_level_temp = [get_db_level(y_band, self.C) for y_band in y_oct.T]
        return oct_level_temp



    def process_audio_files(self, audio_files):
        """Process audio files and calculate SPL levels for each frame of audio data
        :param audio_files:
            List of audio files to process
        :return:
            List of SPL levels for each frame of audio data"""
        
        col_names = ['LA', 'LC', 'LZ', 'LAmax', 'LAmin']
        band_names = [f"{freq:.2f}Hz" for freq in self.third_oct.center_frequencies]
        col_names.extend(band_names)
        all_data = []

        for audio_file in audio_files:
            db = []
            x, _ = sf.read(os.path.join(self.audio_path, audio_file))
            # lfilter_np only supports 1D arrays
            if x.ndim > 1:
                x = x[:, 0]  # or x.mean(axis=1)

            
            name_split = audio_file.split(".")[0]
            start_timestamp = datetime.datetime.strptime(name_split, '%Y%m%d_%H%M%S')
            timestamps = [start_timestamp + datetime.timedelta(seconds=fstart/self.fs) for fstart in range(0, len(x) - self.window_size + 1, self.window_size)]
            
            # A and C weighting to the signal
            # y_A_weighted = lfilter(self.bA, self.aA, x)
            # y_C_weighted = lfilter(self.bC, self.aC, x)


            # y_A_weighted, _ = lfilter_np(self.bA, self.aA, x)
            # y_C_weighted, _ = lfilter_np(self.bC, self.aC, x)


            ziA = None
            ziC = None


            for fstart, timestamp in zip(range(0, len(x) - self.window_size + 1, self.window_size),timestamps):
                frame = x[fstart:fstart + self.window_size]

                yA, ziA = lfilter_np(self.bA, self.aA, frame, zi=ziA)
                yC, ziC = lfilter_np(self.bC, self.aC, frame, zi=ziC)

                LA = round(get_db_level(yA, self.C), 2)
                LC = round(get_db_level(yC, self.C), 2)
                LZ = round(get_db_level(frame, self.C), 2)

                fast_chunk = self.window_size // 8
                fast_levels = [
                    get_db_level(yA[i:i + fast_chunk], self.C)
                    for i in range(0, len(yA) - fast_chunk + 1, fast_chunk)
                ]
                Lmax = round(np.max(fast_levels), 2)
                Lmin = round(np.min(fast_levels), 2)

                oct_level_temp = [round(level, 2) for level in self.get_oct_levels(frame)]

                level_temp = [LA, LC, LZ, Lmax, Lmin] + oct_level_temp + [
                    audio_file, timestamp.strftime('%Y-%m-%d %H:%M:%S')
                ]
                db.append(level_temp)



            # for fstart, timestamp in zip(range(0, len(x) - self.window_size + 1, self.window_size), timestamps):
            #     frame = x[fstart:fstart + self.window_size]
            #     yA = y_A_weighted[fstart:fstart + self.window_size]
            #     yC = y_C_weighted[fstart:fstart + self.window_size]

            #     # levels with weightings
            #     LA = round(get_db_level(yA, self.C), 2)
            #     LC = round(get_db_level(yC, self.C), 2)
            #     LZ = round(get_db_level(frame, self.C), 2)

            #     # LAmax and LAmin over fast intervals
            #     fast_levels = [get_db_level(yA[i:i + self.window_size // 8], self.C) for i in range(0, len(frame) - self.window_size // 8 + 1, self.window_size // 8)]
            #     Lmax = round(np.max(fast_levels), 2)
            #     Lmin = round(np.min(fast_levels), 2)
                
            #     # 1/3 levels
            #     oct_level_temp = [round(level, 2) for level in self.get_oct_levels(frame)]
                
            #     # lists 
            #     level_temp = [LA, LC, LZ, Lmax, Lmin] + oct_level_temp + [audio_file, timestamp.strftime('%Y-%m-%d %H:%M:%S')]
            #     db.append(level_temp)


            # append data end for loop
            all_data.append(db)
            logging.info(f"Processed file: {audio_file}")
        return all_data
    


def read_calibration_constants(ini_file):
    """Read calibration constants from an INI file
    :param ini_file:
        Path to the INI file containing the calibration constants
    :return:
        Dictionary of calibration constants"""
    
    config = configparser.ConfigParser()
    config.read(ini_file)
    logging.info(f"Reading calibration constants from {ini_file}")
    return {key: float(value) for key, value in config['CalibrationConstants'].items()}


def get_device_id(metadata):
    """Get the device ID from the metadata
    :param metadata:
        Metadata object
    :return:
        Device ID
        """
    artist_tags = metadata.tags.get("artist", ["songmeter"])
    if not artist_tags or len(artist_tags[0].split(" ")) < 2:
        return "songmeter"
    logging.info(f"Device ID: {artist_tags[0].split(' ')[1].lower()}")
    return artist_tags[0].split(" ")[1].lower()


def find_audiomoth_folders(base_path):
    """Recursively find all subdirectories containing an 'AUDIOMOTH' folder."""
    for root, dirs, files in os.walk(base_path):
        if 'AUDIOMOTH' in dirs:
            yield root


def parse_arguments():
    parser = argparse.ArgumentParser(description='Calculate SPL levels for audio files in a directory')
    parser.add_argument('-p', '--path', type=str, required=True, help='Directory to be processed')
    return parser.parse_args()


def main():
    r"""
    python leq_levels_oct.py -p "\\192.168.205.117\AAC_Server\PUERTOS\NOISEPORT\20231211_SANTUR\3-Medidas\"
    """
    stable_version = get_stable_version()
    args = parse_arguments()
    base_path = args.path
    calibration_constants = read_calibration_constants('calibration_constants.ini')

    audiomoth_folders = list(find_audiomoth_folders(base_path))
    for subfolder in tqdm(audiomoth_folders[:1], desc='Processing folders'):
        logging.info(f"Processing audio files: {subfolder}...")
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
        # initializing the calculator
        calculator = LeqLevelOct(fs_filterbanks, -10.16, int(fs_filterbanks), audio_path)
        logging.info(f"Processing {len(valid_audio_files)} files in {subfolder}...")
        for audio_file in tqdm(valid_audio_files, desc='Processing audio files'):
            try:
                logging.info(f"Processing file: {audio_file}")
                # select the audio file
                filepath = os.path.join(audio_path, audio_file)
                # read the metadata to get the device_id and eventually get its calibration constant
                metadata = audio_metadata.load(filepath)
                device_id = get_device_id(metadata)
                C = calibration_constants.get(device_id, -10.16)
                calculator.C = C
                # process the audio file
                file_data = calculator.process_audio_files([audio_file])
                # append the data to the list
                all_data_subfolder.extend(file_data)
                logging.info(f"Processed file: {audio_file} with device_id: {device_id} and C: {C} and sample rate: {fs_filterbanks}")
            except Exception as e:
                logging.warning(f'Error processing file: {audio_file}, {e}')



        # save output to CSV
        if all_data_subfolder:
            # setting yp the columns
            col_names = ['LA', 'LC', 'LZ', 'LAmax', 'LAmin'] + [f"{freq:.2f}Hz" for freq in calculator.third_oct.center_frequencies] + ['filename', 'date']
            flat_data = [item for sublist in all_data_subfolder for item in sublist]
            # initializaing the dataframe
            df = pd.DataFrame(flat_data, columns=col_names)
            df = df.sort_values(by='date')
            
            # handling the output directory and final filename
            subfolder = subfolder.split('\\')[-1]
            output_filename = f'leq_oct_{subfolder}_{stable_version}_nm.csv'
            subfolder = subfolder.split('\\')[-1]

            output_folder = audio_path
            output_path = os.path.join(output_folder, output_filename)

            if not os.path.exists(output_folder):
                os.makedirs(output_folder)
                logging.info(f"Creating folder {output_folder}")
            else:
                logging.info(f"Folder {output_folder} already exists")

            # save to CSV            
            df.to_csv(output_path, index=False)
            logging.info(f'Output saved to {output_path}')
            print(f'Output saved to {output_path}')
        else:
            logging.warning(f"No data to save for folder {subfolder}")



if __name__ == '__main__':
    main()