from process_metadata import *
from utils import *
from utils_plot import *
from test_metadata_integrity import *
from logging_config import setup_logging
import json

def main():
    logger = setup_logging()

    # file
    # path = "/home/santi/Documents/AAC/audios/AudioMoths/OCIO/23079_BILBAO_MR_OCIO/BASURTO/AUDIOMOTH/20231019_220640.WAV"
    
    # folder
    # path = "/home/santi/Documents/AAC/audios/AudioMoths/OCIO/23079_BILBAO_MR_OCIO/BASURTO/AUDIOMOTH"
    # path = "/home/santi/Documents/AAC/audios/AudioMoths/PUERTO/PUNTO_3/AUDIOMOTHS"
    # path = r"\\192.168.205.117\AAC_Server\OCIO\Tests\TEST_AUDIOMOTH\BASURTO\AUDIOMOTH"

    # path = "/media/santi/AAC_Deep_Learning/santi_vacaciones/3-Medidas/graneles-nemar-P1/AUDIOMOTH"
    path = "/home/santi/Documents/AAC/audios/AudioMoths/PUERTO/PUNTO_3/AUDIOMOTHS"
    # path = input("Enter the path of the audio file or folder: ")

    logger.info(f"Preprocessing...")
    # make directories
    json_dir, audio_directory, location = make_json_audio_directory(path, logger)

    try:
        # [1] GETTING METADATA
        logger.info("Starting process...")
        metadata = get_metadata(path, logger)
        # logger.info(metadata)

        # save metadata dict to json file
        json_file_name = f"metadata_{location}.json"
        json_path = os.path.join(json_dir, json_file_name)
        
        with open(json_path, "w") as f:
            json.dump(metadata, f, indent=4)
            logger.info(f'Metadata saved in {os.path.join(json_dir, f"{location}_metadata.json")}')


        # [2] TESTING METADATA
        logger.info("Starting testing...")

        logger.info(f"Testing integrity of {location} metadata")
        # [2.1] testing integrity and get valid audio files
        valid_audio_files = test_integrity(metadata, location, logger)

        # [2.2] copy valid audio files to a new folder
        logger.info("Copying audio files with metadata...")
        copy_valid_audio_files_with_metadata(path, audio_directory, valid_audio_files, logger)

        # [2.3] clean metadata
        clean_metadata = get_metadata(audio_directory, logger)
        logger.info(f"There are {len(clean_metadata)} cleaned auduio files in {audio_directory}")
        
        # save to json file
        json_file_name = f"metadata_{location}_clean.json"
        json_path = os.path.join(json_dir, json_file_name)

        with open(json_path, "w") as f:
            json.dump(clean_metadata, f, indent=4)
            logger.info(f'Clean metadata saved in {os.path.join(json_dir, f"{location}_metadata_clean.json")}')
        
        # convert to csv
        df_clean, metadata_folder_path_clean = df_results(clean_metadata, audio_directory, location, logger)
        
        # plot the results
        plot_all_at_one(df_clean, metadata_folder_path_clean, location, logger)
        # plot_standar_deviation(df_clean, metadata_folder_path_clean, location, logger)

    except Exception as e:
        logger.error("Error: %s", e)


if __name__ == "__main__":
    main()
