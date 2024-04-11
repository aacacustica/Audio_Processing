import argparse
import os
from logging_config import setup_logging
import config
from config import *
from sound_data_processing import *


def arg_parser():
    parser = argparse.ArgumentParser(description='Plotting AudioMoth data')
    parser.add_argument('-f', '--path_general', type=str, required=True, help='Path to sonometers folder')
    parser.add_argument('-a', '--agg_period', type=int, required=False, default=900, help='Aggregation period in seconds')
    parser.add_argument('-o', '--output-dir', type=str, required=False, help='Output directory, if not provided, the output directory is the same as the input directory')
    parser.add_argument('-p', '--percentiles', type=float, nargs='+', required=False, default=[90, 10], help='Percentiles to plot [1 5 10 50 90] (L90 and L10 as default)')
    return parser.parse_args()


def main():
    """
    python main.py -f \\192.168.205.117\AAC_Server\OCIO\OCIO_BILBAO\FASE_3
    """
    logger = setup_logging()
    args = arg_parser()
    
    # path to the sonometers folder
    if args.path_general:
        input_folder = args.path_general
    else:
        raise ValueError("Path not provided")

    # aggregation period in seconds, default is 900 seconds (15 minutes)
    if args.agg_period:
        PERIODO_AGREGACION = args.agg_period
    else:
        PERIODO_AGREGACION = config.PERIODO_AGREGACION
    
    # percentiles to plot, default is [90, 10], they are L1, L5, L10, L50, L90
    if args.percentiles:
        PERCENTILES = args.percentiles
    
    yamnet_csv = yamnet_class_map_csv()
    
    input_folder_audiomoth = os.path.join(input_folder, "5-Resultados")
    input_folder_sonometer = os.path.join(input_folder, "3-Medidas")

    # check if the folders exist
    if not os.path.exists(input_folder_audiomoth):
        print(f"Folder {input_folder_audiomoth} does not exist")
    if not os.path.exists(input_folder_sonometer):
        print(f"Folder {input_folder_sonometer} does not exist")

    try:
        # audiomoth
        # get the folders in the input folder
        parent_audiomoth_folders = [folder for folder in os.listdir(input_folder_audiomoth) if os.path.isdir(os.path.join(input_folder_audiomoth, folder))]
        
        # look for the SPL folder inside the folders
        spl_audiomoth_folders = []
        for folder in parent_audiomoth_folders:
            spl_audiomoth_folder = os.path.join(input_folder_audiomoth, folder, "SPL")
            if os.path.exists(spl_audiomoth_folder):
                spl_audiomoth_folders.append(spl_audiomoth_folder)

        # sonometro
        # get the folders in the input folder
        parent_sonometer_folders = [folder for folder in os.listdir(input_folder_sonometer) if os.path.isdir(os.path.join(input_folder_sonometer, folder))]

        # look for the SPL folder inside the folders
        spl_sonometer_folders = []
        for folder in parent_sonometer_folders:
            spl_sonometer_folder = os.path.join(input_folder_sonometer, folder, "SONOMETRO")
            if os.path.exists(spl_sonometer_folder):
                spl_sonometer_folders.append(spl_sonometer_folder)
              
        # process all the folders
        # process_all_folders(input_folder, spl_audiomoth_folders, PERIODO_AGREGACION, PERCENTILES, yamnet_csv, 'AUDIOMOTH', logger)
        process_all_folders(input_folder, spl_sonometer_folders, PERIODO_AGREGACION, PERCENTILES, yamnet_csv, 'SONOMETRO', logger)
        logger.info("Finished sonometer test script")
    except Exception as e:
        logger.exception(f"Error occurred: {e}")
        
if __name__ == "__main__":
    main()