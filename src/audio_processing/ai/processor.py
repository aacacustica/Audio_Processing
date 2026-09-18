import tqdm
import os
import datetime

import numpy as np

from utils_ai import find_audiomoth_folders,save_embeddings_funct,assign_prediction_class,save_predictions_to_csv
from audio_processing.campaign.config import load_config
from audio_processing.common.filesystem import get_audiofiles,get_metadata_audio

config = load_config()

def process_audio_files(classifier, base_path, window_size, threshold, stable_version, save_embeddings, save_spectrogram, model_type,logging):

    col_names               = ['filename','date','class','probability']
    audiomoth_folders       = [find_audiomoth_folders(base_path,config.devices.audiomoth.folder_names)]

    for subfolder in tqdm.tqdm(audiomoth_folders, desc='Processing audiomoth folder'):

        subfolder_name  = os.path.basename(subfolder)
        audio_path      = os.path.join(subfolder,'AUDIOMOTH')

        if not os.path.exists(audio_path):
            logging.warning(f"Skipping {subfolder},{config.devices.audiomoth.folder_names} folder not found")
            continue

        audio_files = get_audiofiles(audio_path)

        if audio_files: 
            logging.info(f"Found { len(audio_files)} audio files.")
        else:
            logging.warning(f"No audio files found in {audio_files}. Skipping.")
            continue

        valid_audio_files = get_metadata_audio(audio_files,audio_path,logging)

        all_data_subfolder          = []
        prediction_per_class_count  = []

        for file in tqdm.tqdm(valid_audio_files,desc='Processing audio files...'):

            prediction_per_file_per_class_count = {}

            try:
                full_path                   = os.path.join(audio_path,file)
                predictions_list,embeddings = classifier.process_single_file(full_path,window_size,save_embeddings,save_spectrogram)

                if save_embeddings:
                    save_embeddings_funct(embeddings,subfolder_name,subfolder,logging)
                    pass

                name_split = file.split(".")[0]
                start_timestamp = datetime.datetime.strptime(name_split, '%Y%m%d_%H%M%S')

                logging.info(f"Classification threshold: {threshold}")

                all_data_subfolder = assign_prediction_class(
                    predictions_list                    =   predictions_list,
                    threshold                           =   threshold,
                    classifier                          =   classifier,
                    prediction_per_class_count          =   prediction_per_class_count,
                    prediction_per_file_per_class_count =   prediction_per_file_per_class_count,
                    start_timestamp                     =   start_timestamp,
                    window_size                         =   window_size,
                    all_data_subfolder                  =   all_data_subfolder,
                    file_name                           =   file)

            except Exception as e:
                logging.error(f"Error processing {file}")
                continue


            if all_data_subfolder: 
                                save_predictions_to_csv(
                                all_data_subfolder  = all_data_subfolder,
                                col_names           = col_names,
                                subfolder_name      = subfolder_name,
                                subfolder           = subfolder,
                                model_type          = model_type,
                                logging             = logging,
                                window_size         = window_size,
                                stable_version      = stable_version
                                )

            else: logging.warning(f"No data to save for folder {subfolder}")

            summary_filename    = f"summary_{config.ai.model}_threshold_{config.ai.threshold}.txt"
            subfolder_path      = base_path.replace(config.outputs.subfolders.general.medidas_folder,config.outputs.subfolders.general.resultados_folder_name)
            output_summary_path = os.path.join(subfolder_path,subfolder_name,config.outputs.subfolders.ai.general_folder_name,config.outputs.subfolders.ai.predictions_folder_name)

            with open(os.path.join(output_summary_path, summary_filename),'w') as f:
            
                        f.write(f"Resumen de precciones del modelo:        {config.ai.model}\n")
                        f.write(f"Del archivo:                             {subfolder}\n")
                        f.write(f"Usando un umbral de:                     {config.ai.threshold}\n")
                        f.write(f"Aplicando una ventana de predicciones de:{config.ai.window_seconds if (config.ai.window_seconds != 0 ) else 'Full audio'} segundos \n")
                        f.write(f"Habiendo procesado un total de:          {len(audiomoth_folders)} archivos\n")
                        f.write(f"Habiendo encontrado un total de:         {len(prediction_per_class_count)} clases con predicciones por encima del umbral\n")
                        f.write(f"\n")
                        f.write("Clases con predicciones por encima del umbral:\n")
                        
                        for class_name, count in prediction_per_class_count.items():
                            f.write(f"{class_name}: {count}\n")
            
            logging.info(f"Summary file saved to: {os.path.join(output_summary_path, summary_filename)}")

        



