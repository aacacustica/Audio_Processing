from pydub import AudioSegment
import pandas as pd
import os

def cut_audio(file_path, output_path, start_time, end_time):
    sound = AudioSegment.from_file(file_path)
    extract = sound[start_time:end_time]
    extract.export(output_path, format="wav")

def process_csv(csv_path):
    # open csv file
    csv = pd.read_csv(csv_path)
    print(csv.head())
    
    # get the file name and start/end time
    # file_paths are in the filename column
    # start/end times are in the start_time_seconds and end_time_seconds columns
    
    for i in range(len(csv)):
        file_path = csv["filename"][i]
        start_time = csv["start_time_seconds"][i]
        end_time = csv["end_time_seconds"][i]
        output_path = "audioset_66_classes/" + file_path.split("/")[-1]
        print("Processing file: " + file_path)
        # cut_audio(file_path, output_path, start_time, end_time)

def main():
    print(os.listdir())
    csv = process_csv("audioset_66_classes.csv")

if __name__ == '__main__':
    main()
