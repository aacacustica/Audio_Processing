import argparse
import os
from logging_config import setup_logging
import config
from config import *
from sound_data_processing import *


def arg_parser():
    parser = argparse.ArgumentParser(description='Plotting AudioMoth data')
    parser.add_argument('-f', '--path_sonometers', type=str, required=False, help='Path to sonometers folder')
    parser.add_argument('-a', '--agg_period', type=int, required=False, default=900, help='Aggregation period in seconds')
    parser.add_argument('-o', '--output-dir', type=str, required=False, help='Output directory, if not provided, the output directory is the same as the input directory')
    parser.add_argument('-p', '--percentiles', type=float, nargs='+', required=False, default=[90, 10], help='Percentiles to plot (L90 and L10 as default)')
    return parser.parse_args()

def main():
    logger = setup_logging()
    args = arg_parser()
    
    # Enter the path to the sonometers folder
    if args.path_sonometers:
        input_folder = args.path_sonometers
    else:
        raise ValueError("Path to sonometers folder not provided")

    # Enter the aggregation period in seconds, default is 900 seconds (15 minutes)
    if args.agg_period:
        PERIODO_AGREGACION = args.agg_period
    else:
        PERIODO_AGREGACION = config.PERIODO_AGREGACION
    
    # Enter the percentiles to plot, default is [90, 10], they are L1, L5, L10, L50, L90
    if args.percentiles:
        PERCENTILES = args.percentiles
    
    # Enter the output directory
    clase_registro = os.path.basename(input_folder)
    # if class is not provided, use the name of the parent folder
    if clase_registro == '':
        clase_registro = os.path.basename(os.path.dirname(input_folder))
    
    try:
        # Get the folders in the input folder
        folders = [folder for folder in os.listdir(input_folder) if os.path.isdir(os.path.join(input_folder, folder))]
        logger.info(f"Found folders: {folders}")
        
        # Process all the folders
        process_all_folders(input_folder, folders, PERIODO_AGREGACION, PERCENTILES, logger)
        
        logger.info("Finished sonometer test script")

    except Exception as e:
        logger.exception(f"Error occurred: {e}")
        
        
if __name__ == "__main__":
    main()