import argparse
import os
from logging_config import setup_logging
import config
from config import *
from processing import *


def arg_parser():
    parser = argparse.ArgumentParser(description='Plotting AudioMoth data')
    parser.add_argument('-f', '--path_general', type=str, required=True, help='Path to sonometers folder')
    parser.add_argument('-a', '--agg_period', type=int, required=False, default=900, help='Aggregation period in seconds')
    parser.add_argument('-o', '--output-dir', type=str, required=False, help='Output directory, if not provided, the output directory is the same as the input directory')
    parser.add_argument('-p', '--percentiles', type=float, nargs='+', required=False, default=[90, 10], help='Percentiles to plot [1 5 10 50 90] (L90 and L10 as default)')
    # argument for audiomoth processing
    parser.add_argument('--audiomoth', action='store_true', help='Process audiomoth data')
    # argument for sonometer processing
    parser.add_argument('--sonometer', action='store_true', help='Process sonometer data')
    return parser.parse_args()


def main():
    """
    python main.py -f \\192.168.205.117\AAC_Server\OCIO\OCIO_BILBAO\FASE_3
    """
    logger = setup_logging()
    args = arg_parser()
    yamnet_csv = yamnet_class_map_csv()    
    
    if args.path_general:
        input_folder = args.path_general
    else:
        raise ValueError("Path not provided")
    if args.agg_period:
        PERIODO_AGREGACION = args.agg_period
    else:
        PERIODO_AGREGACION = config.PERIODO_AGREGACION
    if args.percentiles:
        PERCENTILES = args.percentiles


    try:
        folder_coefficients = {}
        
        # audiomoth
        if args.audiomoth:
            logger.info("Processing audiomoth data")
            spl_audiomoth_folders = []

            for root, dirs, files in os.walk(input_folder):
                if "AUDIOMOTH" in dirs:

                    spl_audiomoth_folder = os.path.join(root, "AUDIOMOTH")
                    if os.path.exists(spl_audiomoth_folder):
                        coeff = float(input(f"Enter correction coefficient for {spl_audiomoth_folder}: "))
                        folder_coefficients[spl_audiomoth_folder] = coeff
                        spl_audiomoth_folders.append(spl_audiomoth_folder)
            
            process_all_folders(input_folder, spl_audiomoth_folders, PERIODO_AGREGACION, PERCENTILES, yamnet_csv, 'AUDIOMOTH', folder_coefficients, logger)


        # sonometro
        if args.sonometer:
            logger.info("Processing sonometer data")
            spl_sonometer_folders = []

            for root, dirs, files in os.walk(input_folder):
                if 'SONOMETRO' in dirs:
                    spl_sonometer_folder = os.path.join(root, "SONOMETRO")
                    if os.path.exists(spl_sonometer_folder):
                        coeff = float(input(f"Enter correction coefficient for {spl_sonometer_folder}: "))
                        folder_coefficients[spl_sonometer_folder] = coeff
                        spl_sonometer_folders.append(spl_sonometer_folder)

            process_all_folders(input_folder, spl_sonometer_folders, PERIODO_AGREGACION, PERCENTILES, yamnet_csv, 'SONOMETRO', folder_coefficients, logger)
        

        logger.info("Finished sonometer test script")
    except Exception as e:
        logger.exception(f"Error occurred: {e}")
        

if __name__ == "__main__":
    main()