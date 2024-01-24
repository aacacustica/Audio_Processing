import os
import numpy as np
import pandas as pd
import soundfile as sf
from datetime import datetime
import configparser
from scipy.signal import lfilter
import audio_metadata
from pyfilterbank.splweighting import a_weighting_coeffs_design, c_weighting_coeffs_design
from utils import *
import argparse
import logging
from tqdm import tqdm
from colorama import init, Fore, Style

"""
Usage:

    python leq_level_class.py -p \\192.168.205.117\AAC_Server\22903-NoiseTech\3-Medidas\
"""


logging.basicConfig(filename='leq_levels.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class AudioProcessor:
    def __init__(self, directory_path, calibration_file='calibration_constants.ini'):
        self.directory_path = directory_path
        self.calibration_file = calibration_file
        self.config = configparser.ConfigParser()
        self.config.read(calibration_file)
        self.calibration_dict = {k: float(v) for k, v in self.config['CalibrationConstants'].items()}

    @staticmethod
    def get_weighting_coeffs(fs_filterbanks):
        bA, aA = a_weighting_coeffs_design(fs_filterbanks)
        bC, aC = c_weighting_coeffs_design(fs_filterbanks)
        return bA, aA, bC, aC

    @staticmethod
    def process_frame(frame, bA, aA, bC, aC, C, w_fast_samples):
        yA = lfilter(bA, aA, frame)
        yC = lfilter(bC, aC, frame)
        LA = get_db_level(yA, C)
        LC = get_db_level(yC, C)
        LZ = get_db_level(frame, C)
        fast_levels = [get_db_level(yA[idx_start:idx_start + w_fast_samples], C)
                       for idx_start in range(0, len(frame) - w_fast_samples + 1, w_fast_samples)]
        return [LA, LC, LZ, np.max(fast_levels), np.min(fast_levels)]

    def process_audio_files(self, audio_file, fs_filterbanks, w_size, C, bA, aA, bC, aC):
        x, _ = sf.read(audio_file)
        w_fast_samples = int(w_size / 8)
        return [self.process_frame(x[fstart:fstart + w_size], bA, aA, bC, aC, C, w_fast_samples)
                for fstart in range(0, len(x) - w_size + 1, w_size)]
    
    @staticmethod
    def save_levels_to_csv(db, audio_file, directory_name, result_dir=None):
        col_names = ['LA', 'LC', 'LZ', 'LAmax', 'LAmin']
        db = np.round(np.array(db), 2)
        
        name_parts = os.path.basename(audio_file).split(".")
        if len(name_parts) < 2:
            raise ValueError(f"Unexpected filename format for {audio_file}")
        name = name_parts[0]
        logging.info(f"Saving levels to CSV for {name}")
        
        df_history = pd.DataFrame(db, columns=col_names)
        df_history['filename'] = name + ".wav"
        
        start = datetime.strptime(name, '%Y%m%d_%H%M%S')
        # name = name.split("_")[0]
        # start = datetime.strptime(name, '%y%m%d')

        df_history['date'] = pd.date_range(start=start, freq='S', periods=len(df_history))
        
        csv_name = f'{directory_name}_spl.csv'
        sub_folder_name = f"{directory_name}_spl"
        logging.info(f"CSV name: {csv_name}")
        logging.info(f"Sub folder name: {sub_folder_name}")
        
        if result_dir:
            directory_path = os.path.join(result_dir, sub_folder_name)
            logging.info(f"Directory path: {directory_path}")
            
            if not os.path.exists(directory_path):
                os.makedirs(directory_path)
                logging.info(f"Created directory: {directory_path}")
            csv_name = os.path.join(directory_path, csv_name)
            logging.info(f"CSV join path name: {csv_name}")
        
        else:
            # 1 directory to save the results = 5-Resultados
            result_dir_name = "5-Resultados"
            spl_extention = "_spl.csv"
            
            # second_parent_dir = parent_dir.split("\\")[:-1]
            
            # join the path
            # resultados_dir = os.path.join('\\\\',*second_parent_dir, result_dir_name)
            # print(f"Resultados_dir --> {resultados_dir}")

            parent_dir = os.path.dirname(audio_file)
            logging.info(f"Parent dir: {parent_dir}")
            
            resultados_dir = parent_dir.split("\\")[:-3]
            logging.info(f"Resultados_dir --> {resultados_dir}")
            
            # join the path
            resultados_dir = os.path.join('\\\\',*resultados_dir, result_dir_name)
            logging.info(f"Resultados_dir join path --> {resultados_dir}")
            
            if not os.path.exists(resultados_dir):
                os.makedirs(resultados_dir)
                logging.info(f"Created directory: {resultados_dir}")
                
            folder_name = parent_dir.split("\\")[-2]
            logging.info(f"Folder name: {folder_name}")
            # exit()            
            if not os.path.exists(os.path.join(resultados_dir, folder_name)):
                os.makedirs(os.path.join(resultados_dir, folder_name))
                logging.info(f"Created directory: {os.path.join(resultados_dir, folder_name)}")
            
            # add SPL folder
            spl_folder_result = os.path.join(resultados_dir, folder_name, 'SPL')
            logging.info(f"SPL folder result: {spl_folder_result}")
            if not os.path.exists(spl_folder_result):
                os.makedirs(spl_folder_result)
                logging.info(f"Created directory: {spl_folder_result}")
            
            # fodler name, is the same as the csv final name
            csv_name = folder_name + spl_extention
            logging.info(f"CSV FINALname: {csv_name}")
            csv_path = os.path.join(spl_folder_result, csv_name)
            logging.info(f"CSV FINAL path: {csv_path}")
            

        df_history.to_csv(csv_path, mode='a', header=not os.path.exists(csv_path), index=False)
        return csv_name

    @staticmethod
    def sort_csv_by_date(filename):
        try:
            logging.info(f"Sorting CSV file {filename} by date.")
            df = pd.read_csv(filename, parse_dates=['date'])
            df_sorted = df.sort_values('date')
            df_sorted.to_csv(filename, index=False)
        except Exception as e:
            logging.error(f"Error sorting the CSV: {str(e)}")

    def get_device_id(self, metadata):
        artist_tags = metadata.tags.get("artist", ["songmeter"])
        if not artist_tags or len(artist_tags[0].split(" ")) < 2:
            return "songmeter"
        return artist_tags[0].split(" ")[1].lower()

    def process_audio(self, audio_file, predominant_fs):
        full_path = os.path.join(self.directory_path, audio_file)
        try:
            metadata = audio_metadata.load(full_path)
            device_id = self.get_device_id(metadata)
            C = self.calibration_dict.get(device_id, -10.16)
            logging.info(f"For audio file {audio_file}, 'C' is set to: {C}")

            bA, aA, bC, aC = self.get_weighting_coeffs(predominant_fs)
            db = self.process_audio_files(full_path, predominant_fs, int(predominant_fs), C, bA, aA, bC, aC)
            csv_name = self.save_levels_to_csv(db, full_path, os.path.basename(os.path.normpath(self.directory_path)), args.result_dir)
            print(f"CSV file saved: {csv_name}")
            self.sort_csv_by_date(csv_name)
            return C
        except Exception as e:
            logging.error(f'Error processing {audio_file}: {str(e)}')
            return None

    def process_directory(self):
        audio_files = [f for f in os.listdir(self.directory_path) if f.lower().endswith('.wav')]
        logging.info(f"Found {len(audio_files)} audio files in the given directory {self.directory_path}.")

        if not audio_files:
            logging.warning("No audio files found in the given directory.")
            return

        # colored text for tqdm description
        print()
        sample_rates = []
        for audio_file in tqdm(audio_files, desc=f"{Fore.YELLOW}{Style.BRIGHT}Collecting sample rates{Style.RESET_ALL}", colour="yellow"):  
            full_path = os.path.join(self.directory_path, audio_file)
            try:
                metadata = audio_metadata.load(full_path)
                sample_rates.append(metadata.streaminfo.sample_rate)
            except Exception as e:
                logging.warning(f"Failed to get sample rate for {audio_file}: {str(e)}")

        predominant_fs = max(set(sample_rates), key=sample_rates.count)
        logging.info(f"Predominant sample rate across files is: {predominant_fs} Hz.")

        # color the print statement
        print(f"\n{Style.BRIGHT}Predominant sample rate across files: {Fore.GREEN}{Style.BRIGHT}{predominant_fs} Hz\n")

        c_constants = [self.process_audio(audio_file, predominant_fs) for audio_file in tqdm(audio_files, desc=f"{Fore.YELLOW}{Style.BRIGHT}Processing audio files{Style.RESET_ALL}", colour="cyan")]
        unique_c_values = set(c_constants)
        default_constant = -10.16

        if len(unique_c_values) == 1:
            const_value = list(unique_c_values)[0]
            message = f"\n{Style.BRIGHT}All audio files use the same C constant: {Fore.GREEN}{const_value}{Style.RESET_ALL}"
            if const_value == default_constant:
                message = f"\n{Style.BRIGHT}No C constant was found. The default C constant {Fore.GREEN}{const_value}{Style.RESET_ALL}{Style.BRIGHT} was used for all devices.{Style.RESET_ALL}"
            print(message + "\n")
        else:
            print(f"\n{Style.BRIGHT}Different C constants were used: {Fore.GREEN}{unique_c_values}{Style.RESET_ALL}\n")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Process audio files for LA, LC, LZ, LAmax, and LAmin levels.")
    parser.add_argument("-p", "--path", required=True, help="Directory path containing the audio files to process.")
    parser.add_argument("-c", "--calibration", default="calibration_constants.ini", help="Calibration constants file path. Defaults to 'calibration_constants.ini'.")
    parser.add_argument("-r", "--result-dir", default=None, help="Directory where the resulting CSV files should be saved. If not specified, it saves in the default directory.")

    args = parser.parse_args()
    init(autoreset=True)
    try:
        processor = AudioProcessor(args.path, args.calibration)
        processor.process_directory()

    except Exception as e:
        logging.critical(f"Critical error occurred: {str(e)}")
        print(f"Critical error occurred: {str(e)}")
