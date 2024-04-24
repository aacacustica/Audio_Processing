import tensorflow as tf
import os
import logging
import pandas as pd
import time
import numpy as np
import subprocess
from tensorboard.plugins import projector
import matplotlib.pyplot as plt
from params import Params


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
        output_filename = f'{subfolder_name}_w_{window_size}s_{stable_version}.csv'
    else:
        output_filename = f'{subfolder_name}_{stable_version}.csv'
    
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
    logging.info("Saving embeddings to tensorboard...")
    
    log_dir = os.path.join(result_folder, subfolder_name, 'AI_MODEL', 'Embeddings')
    os.makedirs(log_dir, exist_ok=True)  # Ensure the directory exists

    # Save the embeddings as a variable in a TensorFlow checkpoint
    embedding_var = tf.Variable(embeddings, name='yamnet_embeddings')
    checkpoint = tf.train.Checkpoint(embedding=embedding_var)
    checkpoint_path = checkpoint.save(os.path.join(log_dir, 'embedding.ckpt'))

    # Prepare metadata file for TensorBoard embeddings projector
    metadata_file = os.path.join(log_dir, 'metadata.tsv')
    with open(metadata_file, 'w') as metadata_writer:
        for index in range(len(embeddings)):
            metadata_writer.write(f"{index}\n")

    # Setup the projector config for visualizing embeddings in TensorBoard
    config = projector.ProjectorConfig()
    embedding_config = config.embeddings.add()
    embedding_config.tensor_name = embedding_var.name
    embedding_config.metadata_path = 'metadata.tsv'
    
    # Save the config file in the log directory
    projector.visualize_embeddings(log_dir, config)

    logging.info(f"Embeddings and metadata saved in {log_dir}")



def save_spectrogram_funct(spectrograms, scores, yamnet_classes, subfolder_name, result_folder, filename):
    logging.info("Saving spectrogram...")
    print(filename)
    params = Params()
    
    log_dir = os.path.join(result_folder, subfolder_name, 'AI_MODEL', 'Spectrograms')
    os.makedirs(log_dir, exist_ok=True)

    # convert lists of tensors or arrays to a single array
    if isinstance(scores, list):
        scores = np.concatenate([score.numpy() if hasattr(score, 'numpy') else np.array(score) for score in scores], axis=0)
        logging.info(f"Concatenated Scores shape: {scores.shape}")
    elif hasattr(scores, 'numpy'):
        scores = scores.numpy()

    logging.info(f"Final Scores shape: {scores.shape}")

    # check if scores are one-dimensional and adjust
    if scores.ndim == 1:
        scores = scores[np.newaxis, :]  # ad a new axis to make it two-dimensional
        logging.info(f"Adjusted Scores shape for plotting: {scores.shape}")

    if isinstance(spectrograms, list):
        spectrogram = np.concatenate([spec.numpy() if hasattr(spec, 'numpy') else np.array(spec) for spec in spectrograms], axis=1)
        logging.info(f"Spectrogram shape: {spectrogram.shape} \nSpectrogram type: {type(spectrogram)}")
    elif hasattr(spectrograms, 'numpy'):
        spectrogram = spectrograms.numpy()
        logging.info(f"Spectrogram shape: {spectrogram.shape} \nSpectrogram type: {type(spectrogram)}")
    

    # Visualize the results.
    plt.figure(figsize=(12, 10))
    plt.suptitle(f"YAMNet predictions for {filename} in folder {subfolder_name}", fontsize=16)
    # # Plot the log-mel spectrogram (returned by the model).
    plt.subplot(2, 1, 1)
    plt.imshow(spectrogram.T, aspect='auto', interpolation='nearest', origin='lower')
    # Plot and label the model output scores for the top-scoring classes.
    mean_scores = np.mean(scores, axis=0)
    top_N = 10
    top_class_indices = np.argsort(mean_scores)[::-1][:top_N]
    plt.subplot(2, 1, 2)
    plt.imshow(scores[:, top_class_indices].T, aspect='auto', interpolation='nearest', cmap='gray_r')
    # Compensate for the patch_window_seconds (0.96s) context window to align with spectrogram.
    patch_padding = (params.patch_window_seconds / 2) / params.patch_hop_seconds
    plt.xlim([-patch_padding, scores.shape[0] + patch_padding])
    # Label the top_N classes.
    yticks = range(0, top_N, 1)
    plt.yticks(yticks, [yamnet_classes[top_class_indices[x]] for x in yticks])
    _ = plt.ylim(-0.5 + np.array([top_N, 0]))
    plt.tight_layout()
    plt.show()
    exit()
    
    # Save the plot
    # output_filename = filename.replace('.wav', '').replace('.WAV', '') + '_spectrogram.png'
    # output_path = os.path.join(log_dir, output_filename)
    # plt.savefig(output_path)
    # plt.close()
    # logging.info(f'Spectrogram saved to {output_path}')




def save_spectrogram_w_funct(spectrogram, scores, yamnet_classes, file_name, start_idx=None, end_idx=None):
    logging.info("Saving spectrogram for window size...")
    
    filename = file_name.split('\\')[-1]
    folder_resultados = file_name.replace('3-Medidas', '5-Resultados')
    folder_resultados = '\\'.join(folder_resultados.split('\\')[:-2])
    folder_resultados = os.path.join(folder_resultados, 'AI_MODEL', 'Spectrograms')

    params = Params()

    # # Handle different formats of scores
    # if isinstance(scores, list):
    #     scores = np.concatenate([score.numpy() if hasattr(score, 'numpy') else np.array(score) for score in scores], axis=0)
    # elif hasattr(scores, 'numpy'):
    #     scores = scores.numpy()

    # # Ensure scores are two-dimensional
    # if scores.ndim == 1:
    #     scores = scores[np.newaxis, :]  # Add a new axis if it's 1D

    # # Handle different formats of spectrograms
    # if isinstance(spectrograms, list):
    #     spectrogram = np.concatenate([spec.numpy() if hasattr(spec, 'numpy') else np.array(spec) for spec in spectrograms], axis=1)
    # elif hasattr(spectrograms, 'numpy'):
    #     spectrogram = spectrograms.numpy()
    # elif isinstance(spectrograms, np.ndarray):
    #     spectrogram = spectrograms  #take this if directly if already an ndarray
    # else:
    #     raise ValueError("Invalid spectrogram format")

    logging.info(f"Spectrogram shape: {spectrogram.shape}")

    # Visualization
    plt.figure(figsize=(12, 10))
    if start_idx is not None and end_idx is not None:
        plt.suptitle(f"YAMNet predictions for {filename} from {start_idx} to {end_idx}", fontsize=16)
    else:
        plt.suptitle(f"YAMNet predictions for {filename}", fontsize=16)

    # Plot the log-mel spectrogram
    plt.subplot(2, 1, 1)
    plt.imshow(spectrogram.T, aspect='auto', interpolation='nearest', origin='lower')
    plt.colorbar(label='Intensity (dB)')
    plt.ylabel('Frequency (Hz)')
    plt.xlabel('Time (seconds)')

    # Plot scores for top-scoring classes
    mean_scores = np.mean(scores, axis=0)
    top_N = 10
    top_class_indices = np.argsort(mean_scores)[::-1][:top_N]
    plt.subplot(2, 1, 2)
    plt.imshow(scores[:, top_class_indices].T, aspect='auto', interpolation='nearest', cmap='gray_r')
    patch_padding = (params.patch_window_seconds / 2) / params.patch_hop_seconds
    plt.xlim([-patch_padding, scores.shape[0] + patch_padding])

    yticks = range(0, top_N, 1)
    plt.yticks(yticks, [yamnet_classes[i] for i in yticks])
    plt.ylim(-0.5 + np.array([top_N, 0]))
    plt.tight_layout()
    plt.show()
    exit()

    # Save the plot
    output_filename = filename.replace('.wav', '').replace('.WAV', '') + f'_spectrogram_{start_idx}_{end_idx}.png'
    output_path = os.path.join(folder_resultados, output_filename)
    plt.savefig(output_path)
    plt.close()
    logging.info(f'Spectrogram saved to {output_path}')



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