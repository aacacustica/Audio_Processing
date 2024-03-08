import argparse
import os
from logging_config import setup_logging
import config
from config import *
from sound_data_processing import *


def arg_parser():
    """Parse arguments from command line
    Any argument is optional but the path to the sonometers folder
    """    
    parser = argparse.ArgumentParser(description='Plotting AudioMoth data')
    parser.add_argument('-f', '--path_sonometers', type=str, required=True, help='Path to sonometers folder')
    parser.add_argument('-a', '--agg_period', type=int, required=False, default=900, help='Aggregation period in seconds')
    parser.add_argument('-o', '--output-dir', type=str, required=False, help='Output directory, if not provided, the output directory is the same as the input directory')
    parser.add_argument('-p', '--percentiles', type=float, nargs='+', required=False, default=[90, 10], help='Percentiles to plot [1 5 10 50 90] (L90 and L10 as default)')
    return parser.parse_args()

def main():
    """This script plots the noise levels from the sonometers
    
    You need to provide the path to the sonometers folder. The aggregation period in seconds, the percentiles to plot and the output directory are optional.
    This script will create a folder with the same name as the sonometer folder in the output directory.
    Inside the folder, it will create a folder for each sonometer with the plots.
    
    You can run the help command to see the arguments:
    
    python main.py -h
    
    An example of how to run this script from the command line is:
    
    python main.py -f "C:/Users/usuario/Desktop/5-Resultados" -a 900 -p 90 10
    
    """
    logger = setup_logging()
    args = arg_parser()
    
    # path to the sonometers folder
    if args.path_sonometers:
        input_folder = args.path_sonometers
    else:
        raise ValueError("Path to sonometers folder not provided")

    # aggregation period in seconds, default is 900 seconds (15 minutes)
    if args.agg_period:
        PERIODO_AGREGACION = args.agg_period
    else:
        PERIODO_AGREGACION = config.PERIODO_AGREGACION
    
    # percentiles to plot, default is [90, 10], they are L1, L5, L10, L50, L90
    if args.percentiles:
        PERCENTILES = args.percentiles
    
    yamnet_csv = yamnet_class_map_csv()
    
    # output directory
    clase_registro = os.path.basename(input_folder)
    # if class is not provided, use the name of the parent folder
    if clase_registro == '':
        clase_registro = os.path.basename(os.path.dirname(input_folder))
    
    try:
        # get the folders in the input folder
        parent_folders = [folder for folder in os.listdir(input_folder) if os.path.isdir(os.path.join(input_folder, folder))]
        logger.info(f"Found folders: {parent_folders}")
        
        # look for the SPL folder inside the folders
        spl_folders = []
        for folder in parent_folders:
            spl_folder = os.path.join(input_folder, folder, "SPL")
            if os.path.exists(spl_folder):
                spl_folders.append(spl_folder)
                
        # process all the folders
        process_all_folders(input_folder, spl_folders, PERIODO_AGREGACION, PERCENTILES, yamnet_csv, logger)
        
        logger.info("Finished sonometer test script")

    except Exception as e:
        logger.exception(f"Error occurred: {e}")
        
if __name__ == "__main__":
    main()