import pandas as pd
from pydub import AudioSegment
import os
from tqdm import tqdm
from logging_config import setup_logging

def check_output_folder(output_folder, logging):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
        logging.info(f"Output folder created: {output_folder}")

def process_audio_files(csv_path, output_folder, logging):
    check_output_folder(output_folder, logging)

    df = pd.read_csv(csv_path)

    for index, row in tqdm(df.iterrows(), total=df.shape[0]):
        audio_path = row['filename']
        try:
            audio = AudioSegment.from_file(audio_path)
            logging.info(f"Processing audio file: {audio_path}")

            start_time_ms = row['start_time_seconds'] * 1000  # milliseconds
            end_time_ms = row['end_time_seconds'] * 1000  # milliseconds
            
            trimmed_audio = audio[start_time_ms:end_time_ms]
            logging.info(f"Original audio duration: {len(audio) / 1000} seconds")
            logging.info(f"Start time: {start_time_ms / 1000} seconds")
            logging.info(f"End time: {end_time_ms / 1000} seconds")
            logging.info(f"Trimmed audio duration: {len(trimmed_audio) / 1000} seconds")
            
            output_path = os.path.join(output_folder, os.path.basename(audio_path))
            trimmed_audio.export(output_path, format="wav")
        except Exception as e:
            logging.error(f"Failed to process {audio_path}: {e}")

    logging.info("All audio files have been trimmed and saved successfully.")

if __name__ == "__main__":
    logging = setup_logging()

    csv_path = r'C:\Users\GIS2\Documents\santi\GitHub\AAC\AI_Model\Fine-Tuning_Models\66_classes_port\transfer-learning-scratch\yamnet\preprocessing\audioset_66_classes.csv'
    output_folder = r'D:\AUDIOSET_STRONG\train_16k_trimmed_logging'
    
    try:
        process_audio_files(csv_path, output_folder, logging)
    except Exception as e:
        logging.error(f"Failed to complete the audio processing: {e}")
