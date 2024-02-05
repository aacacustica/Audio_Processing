import pandas as pd
from pydub import AudioSegment
import os


csv_path = r'AAC\AI_Model\Fine-Tuning_Models\66_classes_port\transfer-learning-scratch\yamnet\preprocessing\audioset_66_classes.csv'

output_folder = r'D:\AUDIOSET_STRONG\train_16k_trimmed'
if not os.path.exists(output_folder):
    os.makedirs(output_folder)

df = pd.read_csv(csv_path)

for index, row in df.iterrows():
    audio_path = row['filename']
    audio = AudioSegment.from_file(audio_path)
    
    start_time_ms = row['start_time_seconds'] * 1000  # milliseconds
    end_time_ms = row['end_time_seconds'] * 1000  # milliseconds
    
    # trimming
    trimmed_audio = audio[start_time_ms:end_time_ms]
    
    output_path = os.path.join(output_folder, os.path.basename(audio_path))
    trimmed_audio.export(output_path, format="wav")

print("All audio files have been trimmed and saved successfully.")
