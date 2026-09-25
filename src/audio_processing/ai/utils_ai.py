import os
import datetime

import plotly as plt  
import tensorflow as tf
import numpy as np
import pandas as pd

from tensorboard.plugins import projector

def find_audiomoth_folders(base_path,audiomoth_folder_name):

    for root, dirs, files in os.walk(base_path):
        if 'AUDIOMOTH' in dirs:
            yield root


def save_embeddings_funct(embeddings, subfolder_name, subfolder,logging):
    try:
        logging.info("")
        logging.info("Saving embeddings to tensorboard...")
        
        subfolder = subfolder.replace('3-Medidas', '5-Resultados')
        log_dir = os.path.join(subfolder, 'AI_MODEL', 'Embeddings')
        os.makedirs(log_dir, exist_ok=True)

        # save the embeddings as a variable in a TensorFlow checkpoint
        embedding_var = tf.Variable(embeddings, name='yamnet_embeddings')
        checkpoint = tf.train.Checkpoint(embedding=embedding_var)
        checkpoint_path = checkpoint.save(os.path.join(log_dir, 'embedding.ckpt'))

        # prepare metadata file for TensorBoard embeddings projector
        metadata_file = os.path.join(log_dir, 'metadata.tsv')
        with open(metadata_file, 'w') as metadata_writer:
            for index in range(len(embeddings)):
                metadata_writer.write(f"{index}\n")

        # setup the projector config for visualizing embeddings in TensorBoard
        config = projector.ProjectorConfig()
        embedding_config = config.embeddings.add()
        embedding_config.tensor_name = embedding_var.name
        embedding_config.metadata_path = 'metadata.tsv'
        
        # save the config file in the log directory
        projector.visualize_embeddings(log_dir, config)

        logging.info(f"Embeddings and metadata saved in {log_dir}")
    
    except Exception as e:
        logging.warning(f"Error saving embeddings: {e}")


def assign_prediction_class(predictions_list,threshold,classifier,prediction_per_class_count,prediction_per_file_per_class_count,start_timestamp,window_size,all_data_subfolder,file_name):

    for i, prediction in enumerate(predictions_list):
        top_indices = np.argsort(prediction)[::-1][:3]
        
        filtered_classes = []
        filtered_probabilities = []
        for idx in top_indices:
            if prediction[idx] >= threshold:
                filtered_classes.append(classifier.yamnet_classes[idx])
                filtered_probabilities.append(f'{prediction[idx]:.4f}')
                #TESTING-----------------
                if classifier.yamnet_classes[idx] not in prediction_per_class_count:
                    prediction_per_class_count[classifier.yamnet_classes[idx]] = 0
                prediction_per_class_count[classifier.yamnet_classes[idx]] += 1

                if classifier.yamnet_classes[idx] not in prediction_per_file_per_class_count:
                    prediction_per_file_per_class_count[classifier.yamnet_classes[idx]] = 0
                prediction_per_file_per_class_count[classifier.yamnet_classes[idx]] += 1
                #TESTING-----------------
        # adjust timestamp based on window size
        adjusted_timestamp = start_timestamp if window_size is None else start_timestamp + datetime.timedelta(seconds=i*window_size)
        
        selected_class = sorted(filtered_classes)[0] if filtered_classes else 'Sin inferencia'
        selected_prob = sorted(filtered_probabilities)[0] if filtered_probabilities else "Sin inferencia"
        all_data_subfolder.append([
            file_name, 
            adjusted_timestamp.strftime('%Y-%m-%d %H:%M:%S'), 
            selected_class,
            selected_prob
        ])

def save_spectrogram_w_funct(spectrogram, scores, yamnet_classes, file_name, sr,logging, start_idx=None, end_idx=None, window_size=None):
    try:
        logging.info("")
        logging.info("Saving spectrogram for window size...")
        
        folder_resultados = file_name.replace('3-Medidas', '5-Resultados')
        filename = file_name.split('\\')[-1]
        folder_resultados = '\\'.join(folder_resultados.split('\\')[:-2])
        folder_resultados = os.path.join(folder_resultados, 'AI_MODEL', 'Spectrograms')
        os.makedirs(folder_resultados, exist_ok=True)
        if not os.path.exists(folder_resultados):
            logging.info(f"Creating folder {folder_resultados}")
        else:
            logging.info(f"Folder {folder_resultados} already exists")

        # convert start_idx and end_idx from samples to seconds for accurate plotting
        start_time = start_idx / sr if start_idx is not None else None
        end_time = end_idx / sr if end_idx is not None else None

        logging.info(f"Spectrogram shape: {spectrogram.shape}")

        # Visualization
        plt.figure(figsize=(12, 10))
        title = f"YAMNet predictions for {filename}"
        if start_time is not None and end_time is not None:
            title += f" from {start_time:.2f} to {end_time:.2f} seconds"
            logging.info(f"Plotting spectrogram from {start_time:.2f} to {end_time:.2f} seconds")
        plt.suptitle(title, fontsize=16)

        # Plot log-mel spectrogram
        logging.info("Plotting spectrogram!!")
        plt.subplot(2, 1, 1)
        plt.imshow(spectrogram.T, aspect='auto', interpolation='nearest', origin='lower')
        plt.colorbar(label='Intensity (dB)')
        plt.ylabel('Frequency (Hz)')
        plt.xlabel('Time (microseconds)')
        if window_size is not None:
            plt.xlim([0, window_size * 200])
            logging.info(f"Window size: {window_size}")
        else:
            logging.info("No window size specified. Plotting full spectrogram.")

        #calculate real time x-axis for scores plot
        num_frames = scores.shape[0]

        # scores for top-scoring classes
        mean_scores = np.mean(scores, axis=0)
        top_N = 10
        top_class_indices = np.argsort(mean_scores)[::-1][:top_N]
        plt.subplot(2, 1, 2)
        plt.imshow(scores[:, top_class_indices].T, aspect='auto', interpolation='nearest', cmap='gray_r')
        
        if start_time is not None and end_time is not None:
            plt.xticks(np.linspace(0, num_frames - 1, 5), labels=np.round(np.linspace(start_time, end_time, 5), 2))
        else:
            plt.xticks(np.linspace(0, num_frames - 1, 5))

        if window_size is not None:
            plt.xlim([0, num_frames - 1])
            logging.info(f"Window size: {window_size}")
        else:
            logging.info("No window size specified. Plotting full prediction map.")

        yticks = range(0, top_N, 1)
        plt.yticks(yticks, [yamnet_classes[i] for i in yticks])
        plt.ylim(-0.5 + np.array([top_N, 0]))
        plt.tight_layout()
        # plt.show()

        # Save the plot
        if start_idx is not None and end_idx is not None:
            output_filename = filename.replace('.wav', '').replace('.WAV', '') + f'_spectrogram_{start_idx}_{end_idx}.png'
        else:
            output_filename = filename.replace('.wav', '').replace('.WAV', '') + '_spectrogram.png'
        
        output_path = os.path.join(folder_resultados, output_filename)
        plt.savefig(output_path)
        plt.close()
        logging.info(f'Spectrogram saved to {output_path}')
    
    except Exception as e:
        logging.warning(f"Error saving spectrogram: {e}")