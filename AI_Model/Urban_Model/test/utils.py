import tensorflow as tf
import os
import logging
import argparse
import pandas as pd

def setup_gpu():
    physical_devices = tf.config.list_physical_devices('GPU')
    print("\nNum GPUs Available: ", len(physical_devices))
    for device in physical_devices:
        print(device)
        print()
    if physical_devices:
        try:
            tf.config.experimental.set_memory_growth(physical_devices[0], True)
        except RuntimeError as e:
            print(e)
            print()


def parse_arguments():
    parser = argparse.ArgumentParser(description='Make prediction with YAMNet model for audio files in a directory')
    parser.add_argument('-p', '--path', type=str, required=True, help='Directory to be processed')
    parser.add_argument('w', '--window_size', type=float, default=None, help='Window size in seconds for processing audio files. Default is None for processing full audio.')
    return parser.parse_args()


def folder_result(path):
    result_folder = '\\5-Resultados'
    path = path.split('\\')[2:-2]
    path = '\\\\' + '\\'.join(path)
    if not os.path.exists(path):
        logging.warning(f"Skipping {path}, AUDIOMOTH folder not found.")
        return False
    else:
        if not os.path.exists(path + result_folder):
            os.makedirs(path + result_folder)
            logging.info(f"Creating folder {path + result_folder}")
        else:
            result_folder = path + result_folder
            logging.info(f"Folder {result_folder} already exists")
    return result_folder


def save_predictions_to_csv(all_data_subfolder, col_names, subfolder_name, result_folder, window_size=None):
    if window_size is not None:
        output_filename = f'predictions_{subfolder_name}_window_{window_size}s.csv'
    else:
        output_filename = f'predictions_{subfolder_name}.csv'
    
    output_folder = os.path.join(result_folder, subfolder_name, 'AI_MODEL', 'Predictions')
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    output_path = os.path.join(output_folder, output_filename)
    df_subfolder = pd.DataFrame(all_data_subfolder, columns=col_names)
    df_subfolder.to_csv(output_path, index=False)
    logging.info(f'Output saved to {output_path}')
