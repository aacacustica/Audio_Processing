from __future__ import division, print_function

import os
import numpy as np
import tqdm
import resampy
import soundfile as sf
import tensorflow as tf
import logging
from utils import *
from utils_spl import *
import datetime
import audio_metadata
import argparse

import params as yamnet_params
import yamnet as yamnet_model


from pyfilterbank.splweighting import a_weighting_coeffs_design, c_weighting_coeffs_design


logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s', 
    filename='yamnet_inference_test.log', 
    filemode='a'
    )


class LeqLevel:
    def __init__(self, fs, calibration_constant, window_size):
        self.fs = fs
        self.C = calibration_constant
        self.window_size = window_size
        self.bA, self.aA = a_weighting_coeffs_design(fs)
        self.bC, self.aC = c_weighting_coeffs_design(fs)
        self.fast_samples = int(window_size / 8)
        logging.info(f"LeqLevel initialized with fs: {fs}, C: {calibration_constant}, window_size: {window_size}")

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

            db_levels.append([LA, LC, LZ, Lmax, Lmin])
            logging.info(f"Processed frame: {fstart} - {fstart + self.window_size}")
        return np.round(db_levels, 2)


class AudioClassifier:
    def __init__(self):
        self.params = yamnet_params.Params()
        self.yamnet = yamnet_model.yamnet_frames_model(self.params)
        self.yamnet.load_weights('yamnet.h5')
        self.yamnet_classes = yamnet_model.class_names('yamnet_class_map.csv')


    def process_single_file(self, file_path, window_size=None, save_embeddings=False, save_spectrogram=False, save_clips=False):
        # logging.info(f"Processing file: {file_path}")
        wav_data, sr = sf.read(file_path, dtype=np.int16)
        waveform = wav_data / 32768.0  # Convert to [-1.0, +1.0]
        waveform = waveform.astype('float32')

        if len(waveform.shape) > 1:
            waveform = np.mean(waveform, axis=1)
            logging.warning(f"Audio file has more than 1 channel. Taking the mean of all channels.")
        if sr != self.params.sample_rate:
            waveform = resampy.resample(waveform, sr, self.params.sample_rate)
            logging.warning(f"Resampling audio from {sr} to {self.params.sample_rate}")


        # process audio file
        predictions = []
        all_embeddings = []
        if window_size is None and save_clips is False:
            logging.info("Processing whole file without window size")
            logging.info(f"Waveform shape: {waveform.shape}")
            scores, embeddings, spectrogram = self.yamnet(waveform)

            if save_spectrogram:
                scores = scores.numpy()
                spectrogram = spectrogram.numpy()
                save_spectrogram_w_funct(spectrogram, scores, self.yamnet_classes, file_path, self.params.sample_rate)

            prediction = np.mean(scores, axis=0)
            predictions.append(prediction)

            if save_embeddings:
                all_embeddings.append(embeddings.numpy())
            return predictions, all_embeddings


        # process audio file with window size
        else:
            if save_spectrogram:
                logging.info("Entering the window size analysis. But we run the whole audio file to save the complteted spectrogram.")
                scores, embeddings, spectrogram = self.yamnet(waveform)
                scores = scores.numpy()
                spectrogram = spectrogram.numpy()
                save_spectrogram_w_funct(spectrogram, scores, self.yamnet_classes, file_path, self.params.sample_rate)

            if save_clips:
                window_size =  2.5
            logging.info(f"Processing file with window size: {window_size}")
            window_size_samples = int(window_size * sr)

            for start_idx in range(0, len(waveform), window_size_samples):
                end_idx = start_idx + window_size_samples
                if end_idx > len(waveform):
                    end_idx = len(waveform)  # include the last segment
            
                window = waveform[start_idx:end_idx]
                scores, embeddings, spectrogram = self.yamnet(window)
                
                if save_spectrogram:
                    scores = scores.numpy()
                    spectrogram = spectrogram.numpy()
                    save_spectrogram_w_funct(spectrogram, scores, self.yamnet_classes, file_path, self.params.sample_rate, start_idx, end_idx, window_size)

                prediction = np.mean(scores, axis=0)
                predictions.append(prediction)

                if save_embeddings:
                    all_embeddings.append(embeddings.numpy())

                if save_clips:
                    extrac_clips(prediction, window, start_idx, self.params.sample_rate,  self.yamnet_classes, file_path)
            return predictions, all_embeddings
    

# def process_audio_files(classifier, base_path, window_size, threshold, stable_version, save_embeddings, save_spectrogram, save_clips):
#     subfolders = [f.path for f in os.scandir(base_path) if f.is_dir()]
#     result_folder = folder_result(base_path)
    
#     # predictions columns
#     col_names = ['filename', 'date', 'class', 'probability']

#     # spl columns
#     calibration_constants = read_calibration_constants('calibration_constants.ini')
#     col_names_spl = ['LA', 'LC', 'LZ', 'LAmax', 'LAmin', 'filename', 'date']


#     for subfolder in tqdm.tqdm(subfolders, desc='Processing subfolders'):
#         subfolder_name = os.path.basename(subfolder)
#         audio_path = os.path.join(subfolder, "AUDIOMOTH")
#         logging.info(f"Processing subfolder: {subfolder}...")

#         if not os.path.exists(audio_path):
#             logging.warning(f"Skipping {subfolder}, AUDIOMOTH folder not found.")
#             continue
#         audio_files = get_audiofiles(audio_path)
#         if not audio_files:
#             logging.warning(f"No audio files found in: {audio_path}")
#             continue


#         # read metadata
#         sample_rates = []
#         valid_audio_files = []
#         logging.info(f"Reading metadata...")
#         for file in tqdm.tqdm(audio_files[:1], desc='Reading metadata'):
#             try:
#                 metadata = audio_metadata.load(os.path.join(audio_path, file))
#                 sample_rates.append(metadata.streaminfo.sample_rate)
#                 valid_audio_files.append(file)
#             except Exception as e:
#                 logging.warning(f'Error reading file metadata: {file}, {e}')
#         if not sample_rates:
#             logging.warning("No valid audio files to process.")
#             continue
#         if not valid_audio_files:
#             logging.warning(f"No valid audio files to process in {subfolder}")
#             continue
#         logging.info(f'Processing {len(valid_audio_files)} files in {subfolder}')

#         fs_filterbanks = np.median(sample_rates)
#         logging.info(f'Using sample rate: {fs_filterbanks}')


#         all_data_subfolder_spl = []
#         all_data_subfolder_pred = []
#         for file_name in tqdm.tqdm(valid_audio_files, desc='Processing audio files'):
#             try:
#                 # [1] process SPL levels
#                 logging.info(f"Processsing file: {file_name}...")
#                 filepath = os.path.join(audio_path, file_name)
#                 metadata = audio_metadata.load(filepath)
#                 device_id = get_device_id(metadata)
#                 C = calibration_constants.get(device_id, -10.16)
#                 calculator = LeqLevel(fs_filterbanks, C, int(fs_filterbanks))
#                 logging.info(f'Processing file: {file_name} with calibration constant: {C} and sample rate: {fs_filterbanks} Hz')

#                 audio_data, _ = sf.read(filepath)
#                 db_levels = calculator.calculate_spl_levels(audio_data)

#                 if db_levels.shape[1] != 5:
#                     logging.warning(f'Unexpected shape for db_levels: {db_levels.shape} for file {file_name}')
#                     continue

#                 name_split = file_name.split(".")[0]
#                 start_timestamp = datetime.datetime.strptime(name_split, '%Y%m%d_%H%M%S')
#                 timestamps = [start_timestamp + datetime.timedelta(seconds=i) for i in range(db_levels.shape[0])]

#                 for row, timestamp in zip(db_levels, timestamps):
#                     all_data_subfolder_spl.append(list(row) + [file_name, timestamp.strftime('%Y-%m-%d %H:%M:%S')])

#                 # save SPL data
#                 if all_data_subfolder_spl:
#                     df_spl = save_spl_to_csv(all_data_subfolder_spl, col_names_spl, subfolder_name, result_folder, stable_version)
#                     print(df_spl)
#                 else:
#                     logging.warning(f"No SPL data to save for folder {subfolder}")


#                 # [2] making predictions
#                 full_path = os.path.join(audio_path, file_name)
#                 predictions_list, embeddings = classifier.process_single_file(full_path, window_size, save_embeddings, save_spectrogram, save_clips)

#                 if save_embeddings:
#                     save_embeddings_funct(embeddings, subfolder_name, result_folder)

#                 name_split = file_name.split(".")[0]
#                 start_timestamp = datetime.datetime.strptime(name_split, '%Y%m%d_%H%M%S')

#                 threshold = classifier.params.classification_threshold if args.threshold is None else args.threshold
#                 logging.info(f"Classification threshold: {threshold}")

#                 for i, prediction in enumerate(predictions_list):
#                     top_indices = np.argsort(prediction)[::-1][:5]
                    
#                     filtered_classes = []
#                     filtered_probabilities = []
#                     for idx in top_indices:
#                         if prediction[idx] >= threshold:
#                             filtered_classes.append(classifier.yamnet_classes[idx])
#                             filtered_probabilities.append(f'{prediction[idx]:.4f}')

#                     filtered_classes_str = ', '.join(filtered_classes)
#                     filtered_probabilities_str = ', '.join(filtered_probabilities)
#                     # adjust timestamp based on window size
#                     adjusted_timestamp = start_timestamp if window_size is None else start_timestamp + datetime.timedelta(seconds=i*window_size)

#                     all_data_subfolder_pred.append([
#                         file_name, 
#                         adjusted_timestamp.strftime('%Y-%m-%d %H:%M:%S'), 
#                         filtered_classes_str, 
#                         filtered_probabilities_str
#                     ])

#             except Exception as e:
#                 logging.error(f"Error processing file {file_name}: {e}")

#         # save Predictions data
#         if all_data_subfolder_pred:
#             df_pred = save_predictions_to_csv(all_data_subfolder_pred, col_names, subfolder_name, result_folder, window_size, stable_version)
#             print(df_pred)
#         else:
#             logging.warning(f"No Prediction data to save for folder {subfolder}")






def process_audio_files(classifier, base_path, window_size, threshold, stable_version, save_embeddings, save_spectrogram, save_clips):
    subfolders = [f.path for f in os.scandir(base_path) if f.is_dir()]
    result_folder = folder_result(base_path)
    calibration_constants = read_calibration_constants('calibration_constants.ini')
    
    # columns for both SPL and predictions
    col_names = ['filename', 'timestamp', 'LA', 'LC', 'LZ', 'LAmax', 'LAmin', 'class', 'probability']

    for subfolder in tqdm.tqdm(subfolders, desc='Processing subfolders'):
        subfolder_name = os.path.basename(subfolder)
        audio_path = os.path.join(subfolder, "AUDIOMOTH")
        logging.info(f"Processing subfolder: {subfolder}...")

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
        for file in tqdm.tqdm(audio_files[:1], desc='Reading metadata'):
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

        
        # data for both SPL and predictions
        all_data_subfolder = []
        for file_name in tqdm.tqdm(valid_audio_files, desc='Processing audio files'):
            try:
                # [1] SPL levels
                logging.info(f"Processsing SPL for file: {file_name}...")
                filepath = os.path.join(audio_path, file_name)
                metadata = audio_metadata.load(filepath)
                device_id = get_device_id(metadata)
                C = calibration_constants.get(device_id, -10.16)
                calculator = LeqLevel(fs_filterbanks, C, int(fs_filterbanks))
                logging.info(f'Processing file: {file_name} with calibration constant: {C} and sample rate: {fs_filterbanks} Hz')

                audio_data, _ = sf.read(filepath)
                db_levels = calculator.calculate_spl_levels(audio_data)

                # [2] predictions
                logging.info(f"Processsing Prediction for file: {file_name}...")
                full_path = os.path.join(audio_path, file_name)
                predictions_list, embeddings = classifier.process_single_file(full_path, window_size, save_embeddings, save_spectrogram, save_clips)
                if save_embeddings:
                    save_embeddings_funct(embeddings, subfolder_name, result_folder)

                start_timestamp = datetime.datetime.strptime(file_name.split(".")[0], '%Y%m%d_%H%M%S')
                timestamps = [start_timestamp + datetime.timedelta(seconds=i) for i in range(len(db_levels))]

                # spl data and predictions
                threshold = classifier.params.classification_threshold if args.threshold is None else args.threshold
                logging.info(f"Classification threshold: {threshold}")

                for i, (spl_data, prediction) in enumerate(zip(db_levels, predictions_list)):
                    top_indices = np.argsort(prediction)[::-1][:5]
                    logging.info(f"Top indices: {top_indices}")

                    filtered_classes = [classifier.yamnet_classes[idx] for idx in top_indices if prediction[idx] >= threshold]
                    filtered_probabilities = [f'{prediction[idx]:.4f}' for idx in top_indices if prediction[idx] >= threshold]

                    # string the log info
                    logging.info(f"Filtered classes: {', '.join(filtered_classes)}")
                    logging.info(f"Filtered probabilities: {', '.join(filtered_probabilities)}")

                    # making sure that all entries are strings to avoid type conflicts
                    combined_data = [
                        file_name,
                        timestamps[i].strftime('%Y-%m-%d %H:%M:%S')
                    ] + [str(x) for x in spl_data] + [', '.join(filtered_classes), ', '.join(filtered_probabilities)]

                    all_data_subfolder.append(combined_data)

            except Exception as e:
                logging.error(f"Error processing file {file_name}: {e}")

        #save all data to CSV
        if all_data_subfolder:
            df = pd.DataFrame(all_data_subfolder, columns=col_names)
            output_filename = f'combined_data_{subfolder_name}_{stable_version}.csv'
            output_path = os.path.join(result_folder, output_filename)
            df.to_csv(output_path, index=False)
            logging.info(f'Combined data saved to {output_path}')
            print(df)
            print(output_path)
        else:
            logging.warning(f"No data to save for folder {subfolder}")


def parse_arguments():
    parser = argparse.ArgumentParser(description='Make prediction with YAMNet model for audio files in a directory')
    parser.add_argument('-p', '--path', type=str, required=True, help='Directory to be processed')
    parser.add_argument('-w', '--window', type=float, default=None, help='Window size in seconds for processing audio files. Default is None for processing full audio.')
    parser.add_argument('-t', '--threshold', type=float, default=None, help='Classification threshold for predictions.')
    parser.add_argument('--embeddings', action='store_true', help='Save embeddings to tensorboard')
    parser.add_argument('--spectrogram', action='store_true', help='Save spectrogram images')
    parser.add_argument('--clips', action='store_true', help='Save audio clips')
    return parser.parse_args()

if __name__ == '__main__':
    """
    python .\inference_custom.py -p "\\192.168.205.117\AAC_Server\OCIO\OCIO_BILBAO\CAMPAÑA_3\3-Medidas\" -w 1
    """
    setup_gpu()
    stable_version = get_stable_version()
    args = parse_arguments()
    
    # process audio files
    classifier = AudioClassifier()
    process_audio_files(classifier, args.path, args.window, args.threshold, stable_version, args.embeddings, args.spectrogram, args.clips)

    logging.info("Inference completed with success!!!")