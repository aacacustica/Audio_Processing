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
        # GETTING METADATA
        logger.info("Starting process...")
        metadata = get_metadata(path, logger)
        # logger.info(metadata)

        # save to json file
        json_file_name = f"metadata_{location}.json"
        json_path = os.path.join(json_dir, json_file_name)
        
        with open(json_path, "w") as f:
            json.dump(metadata, f, indent=4)
            logger.info(f'Metadata saved in {os.path.join(json_dir, f"{location}_metadata.json")}')


        # TESTING METADATA
        logger.info("Starting testing...")
        # [2] test integrity
        valid_audio_files = test_integrity(metadata, location, logger)

        # copy valid audio files to a new folder
        logger.info("Copying...")
        copy_valid_audio_files_with_metadata(path, audio_directory, valid_audio_files, logger)

        #get the df of the results
        df, metadata_folder_path = df_results(metadata, audio_directory, location, logger)
        print(f"Original metadata: \n{df}")
        print(len(df))

        # plot the results
        # plot_temperature(df, metadata_folder_path, location, logger)
        # plot_battery(df, metadata_folder_path, location, logger)
        # plot_all_at_one(df, metadata_folder_path, location, logger)

        # clean metadata
        print(audio_directory)
        clean_metadata = get_metadata(audio_directory, logger)
        print(f"\n\nClean metadata: \n{clean_metadata}")
        print(len(clean_metadata))
        
        # exit()

        # save to json file
        json_file_name = f"metadata_{location}_clean.json"
        json_path = os.path.join(json_dir, json_file_name)

        with open(json_path, "w") as f:
            json.dump(clean_metadata, f, indent=4)
            logger.info(f'Clean metadata saved in {os.path.join(json_dir, f"{location}_metadata_clean.json")}')
        
        # convert to csv
        df_clean, metadata_folder_path_clean = df_results(clean_metadata, audio_directory, location, logger)
        print(df)
        
        # plot the results
        plot_temperature(df_clean, metadata_folder_path_clean, location, logger)
        plot_battery(df_clean, metadata_folder_path_clean, location, logger)
        plot_all_at_one(df_clean, metadata_folder_path_clean, location, logger)

    except Exception as e:
        logger.error("Error: %s", e)


if __name__ == "__main__":
    main()
