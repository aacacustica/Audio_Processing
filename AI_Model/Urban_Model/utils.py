import tensorflow as tf
import os
import logging
import argparse
import pandas as pd
import time
import numpy as np
import subprocess
from tensorboard.plugins import projector
import matplotlib.pyplot as plt
import params 


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
    parser.add_argument('-w', '--window_size', type=float, default=None, help='Window size in seconds for processing audio files. Default is None for processing full audio.')
    parser.add_argument('--threshold', type=float, default=None, help='Classification threshold for predictions.')
    parser.add_argument('--embeddings', action='store_true', help='Save embeddings to tensorboard')
    parser.add_argument('--spectrogram', action='store_true', help='Save (to plot) spectrogram')
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


def save_predictions_to_csv(all_data_subfolder, col_names, subfolder_name, result_folder, window_size=None, stable_version=None):
    if window_size is not None:
        output_filename = f'predictions_{subfolder_name}_w_{window_size}s_{stable_version}.csv'
    else:
        output_filename = f'predictions_{subfolder_name}_{stable_version}.csv'
    
    output_folder = os.path.join(result_folder, subfolder_name, 'AI_MODEL', 'Predictions')
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    output_path = os.path.join(output_folder, output_filename)

    df_subfolder = pd.DataFrame(all_data_subfolder, columns=col_names)
    # order df by date
    df_subfolder = df_subfolder.sort_values(by='date')
    df_subfolder.to_csv(output_path, index=False)
    logging.info(f'Output saved to {output_path}')



def save_embeddings_funct(embeddings, subfolder_name, result_folder):
    logging.info(f"Saving embeddings to tensorboard...")
    
    log_dir = os.path.join(result_folder, subfolder_name, 'AI_MODEL', 'Embeddings')
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    embedding_var = tf.Variable(embeddings, name='yamnet_embeddings')
    checkpoint = tf.train.Checkpoint(embedding=embedding_var)
    checkpoint.save(os.path.join(log_dir, 'embedding.ckpt'))

    metadata_file = os.path.join(log_dir, 'metadata.tsv')
    with open(metadata_file, 'w') as metadata_writer:
        for index in range(len(embeddings)):
            metadata_writer.write('{}\n'.format(index))

    config = projector.ProjectorConfig()
    embedding_config = config.embeddings.add()
    embedding_config.tensor_name = "embedding/.ATTRIBUTES/VARIABLE_VALUE"
    embedding_config.metadata_path = 'metadata.tsv'
    projector.visualize_embeddings(log_dir, config)

    logging.info(f"Embeddings and metadata saved in {log_dir}")




def save_spectogram_funct(spectrogram, scores, class_names, subfolder_name, result_folder):
    logging.info(f"Saving spectogram to tensorboard...")

    log_dir = os.path.join(result_folder, subfolder_name, 'AI_MODEL', 'Spectrogram')
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)    


    plt.figure(figsize=(10, 8))
    # Plot the log-mel spectrogram (returned by the model).
    plt.subplot(2, 1, 2)
    plt.imshow(spectrogram.T, aspect='auto', interpolation='nearest', origin='lower')

    # Plot and label the model output scores for the top-scoring classes.
    mean_scores = np.mean(scores, axis=0)
    top_N = 10
    top_class_indices = np.argsort(mean_scores)[::-1][:top_N]
    plt.subplot(2, 1, 3)
    plt.imshow(scores[:, top_class_indices].T, aspect='auto', interpolation='nearest', cmap='gray_r')
    
    # Compensate for the patch_window_seconds (0.96s) context window to align with spectrogram.
    patch_padding = (params.patch_window_seconds / 2) / params.patch_hop_seconds
    plt.xlim([-patch_padding, scores.shape[0] + patch_padding])
    
    # Label the top_N classes.
    yticks = range(0, top_N, 1)
    plt.yticks(yticks, [class_names[top_class_indices[x]] for x in yticks])
    _ = plt.ylim(-0.5 + np.array([top_N, 0]))

    # save the plot
    plt.savefig(os.path.join(log_dir, f'spectrogram_{subfolder_name}.png'))



def print_top_predictions(file_name, predictions, class_names, top_n=5):
    print(f"\nTop {top_n} predictions for {file_name}:")
    top_indices = np.argsort(predictions)[::-1][:top_n] 
    
    for rank, idx in enumerate(top_indices, start=1):
        class_name = class_names[idx]
        probability = predictions[idx]
        print(f"{rank}. {class_name}: {probability:.4f}")
        time.sleep(1)  


def get_audiofiles(path):
    audio_files = [file for file in os.listdir(path) if file.lower().endswith('.wav')]
    return audio_files


def list_git_tags():
    try:
        tags = tags = subprocess.check_output(["git", "tag"]).strip().decode()
        return tags.split('\n')
    except subprocess.CalledProcessError:
        return None
    

def select_tag(tags):
    for i, tag in enumerate(tags):
        logging.info(f"{i}: {tag}")
    choice = int(input("Select the tag to use: "))
    tag_selected = tags[choice]
    # replace "." with "_" to be able to use it as a file name
    tag_selected = tag_selected.replace(".", "_")
    return tag_selected


def get_stable_version():
    tags = list_git_tags()
    # get the latest stable version
    tag_selected = tags[-1]
    logging.info(f"Latest stable version: {tag_selected}")
    # replace "." with "_" to be able to use it as a file name
    tag_selected = tag_selected.replace(".", "_")
    logging.info(f"Latest stable version string: {tag_selected}")
    return tag_selected