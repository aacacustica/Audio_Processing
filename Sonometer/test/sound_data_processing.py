import pandas as pd
import matplotlib.pyplot as plt
import os
plt.style.use("bmh")
from sound_data_visualization import *
from sound_data_reader import *
from time_level_utils import *
from config import *
from tqdm import tqdm

def load_data(file_path, logger):
    """Loading data from file_path and returning a dataframe with the data and the SLM type
    Args:
        file_path (str): Path to the file to load
        logger (logging.Logger): Logger object
        Returns:
            df (pd.DataFrame): Dataframe with the data
            slm_type (str): SLM type
            slm_dict (dict): Dictionary with the columns names for the SLM type
    """
    
    slm_type_function_mapping = {
        "814": (get_data_814, larson814_dict),
        "824": (get_data_824, larson824_dict),
        "lx_ES": (get_data_lx_ES, larsonlx_dict),
        "lx_EN": (get_data_lx_EN, larsonlx_dict),
        "SV307": (get_data_SV307, SV307_dict),
        "cesva": (get_data_cesva, cesva_dict),
        "audio-post": (get_data_audio, audiopost_dict)
    } # SLM stands for Sound Level Meter
    
    logger.info(f"Analizing {file_path}")
    # Try to load the data for each SLM type until one works |  for each slm_type, (func, slm_dict) in slm_type_function_mapping.items(): means that for each key and value in the dictionary, the key is slm_type and the value is a tuple with the function and the dictionary | the function is the function to load the data and the dictionary is the dictionary with the column names for the SLM type
    for slm_type, (func, slm_dict) in slm_type_function_mapping.items():
        try:
            logger.info(f"Loading data for SLM type {slm_type}")
            df = func(file_path)
            return df, slm_type, slm_dict
        
        except Exception as e:
            clean_message = str(e).replace('\n', ' ')  # Replace newlines with spaces
            logger.warning(f"Failed to load data for SLM type {slm_type}: {clean_message}. Trying next SLM type")
            continue
    raise ValueError("SLM type not found or file could not be loaded")

def process_folder(folder_path, logger):
    """Process a folder containing the measurement files
    Args:
        folder_path (str): Path to the folder containing the measurement files
        logger (logging.Logger): Logger object
    Returns:
        df (pd.DataFrame): Dataframe with the data
        slm_type (str): SLM type
        slm_dict (dict): Dictionary with the columns names for the SLM type
    """
    
    # Check if the folder contains a CESVA folder
    cesva_path = os.path.join(folder_path, 'CESVA')
    if os.path.isdir(cesva_path):
        # If it does, load the data from the CESVA folder
        subfolders = [f for f in os.listdir(cesva_path) if os.path.isdir(os.path.join(cesva_path, f))]
        # Check if the CESVA folder contains subfolders
        for subfolder in subfolders:
            # If it does, load the data from the first subfolder
            subfolder_path = os.path.join(cesva_path, subfolder)
            # Check if the subfolder contains measurement files
            files = [os.path.join(subfolder_path, f) for f in os.listdir(subfolder_path) if f.endswith(('.csv', '.xlsx', '.CSV', 'XLSX'))]
            # If it does, load the data from the first measurement file
            if files:
                return load_data(files[0], logger)  
            else:
                logger.warning(f"No measurement files found in {subfolder_path}")
    else:
        files = [os.path.join(folder_path, f) for f in os.listdir(folder_path) if f.endswith(('.csv', '.xlsx', '.CSV'))]
        logger.info(f"Files found: {files}")
        if not files:
            logger.warning(f"No measurement files found in {folder_path}")
            return None, None, None
        return load_data(files[0], logger) 
    return None, None, None 


def process_all_folders(input_folder, folders, PERIODO_AGREGACION, PERCENTILES, logger):
    """Process all the folders in the input folder
    Args:
        input_folder (str): Path to the input folder
        folders (list): List of folders to process
        PERIODO_AGREGACION (int): Aggregation period in seconds
        PERCENTILES (list): Percentiles to plot
        logger (logging.Logger): Logger object
    Returns:
            df_indicadores (pd.DataFrame): Dataframe with the indicators
            df_common_format (pd.DataFrame): Dataframe with the data in a common format
    """
    # Process each folder
    for folder in tqdm(folders, desc="Processing folders"):
        logger.info(f"Processing folder: {folder}")
        # Get the path to the folder
        reg_folder = os.path.join(input_folder, folder)

        # Create the output folder
        folder_output_dir = os.path.join(reg_folder, "Results", "Sonometer_plots")
        os.makedirs(folder_output_dir, exist_ok=True)

        try:
            # df, slm_type, slm_dict = process_folder(reg_folder, logger)
            df, slm_dict = process_folder(reg_folder, logger)
            if df is None:
                continue

            # Add datetime columns, sort by datetime and set datetime as index
            df = add_datetime_columns(df, date_col='datetime') 
            df = df.sort_values('datetime')
            df.set_index('datetime', inplace=True)
            start_date = df.index[0]
            end_date = df.index[-1]
            
            # drop the beginning and ending of the measurement (15min)
            try:
                df = df.loc[start_date + pd.Timedelta(900, unit='seconds'):end_date - pd.Timedelta(900, unit='seconds')]
            except:
                continue

            #df['oca'] = df.apply(lambda x: db_limit(x['hour'],ld_limit= LIMITE_DIA , le_limit= LIMITE_TARDE ,ln_limit= LIMITE_NOCHE) , axis=1)
            #print(df)

            # Plotting time plot
            if PLOT_MAKE_TIME_PLOT:
                logger.info(f"Plotting time plot for folder {folder}")
                make_time_plot(df, folder_output_dir, logger, columns_dict=slm_dict, agg_period=PERIODO_AGREGACION, plotname=folder, percentiles=PERCENTILES)
            
            # Plotting heatmap
            if PLOT_HEATMAP_EVOLUTION:
                logger.info(f"Plotting heatmap for folder {folder}")
                plot_heatmap_evolution(df, folder_output_dir, logger, values_column=slm_dict['LAEQ_COLUMN'], agg_func=leq,plotname=folder)
            
            # Plotting day evolution
            if PLOT_DAY_EVOLUTION:
                logger.info(f"Plotting day evolution for folder {folder}")
                plot_day_evolution(df, folder_output_dir, logger, laeq_column=slm_dict["LAEQ_COLUMN"], plotname=folder)

            # add indicators column
            df['indicador_str'] = df.apply(lambda x: evaluation_period_str(x['hour']), axis=1)
            
            # Plotting period evolution
            if PLOT_PERIOD_EVOLUTION:
                logger.info(f"Plotting period evolution for folder {folder}")
                plot_period_evolution(df, folder_output_dir, logger, laeq_column=slm_dict["LAEQ_COLUMN"], plotname=folder)
            
            # Plotting individual heatmap
            if PLOT_INDICADORES_HEATMAP:
                logger.info(f"Plotting indicadores heatmap for folder {folder}")
                plot_indicadores_heatmap(df, folder_output_dir, logger, plotname=folder, ind_column=slm_dict["LAEQ_COLUMN"])
                
            # add nights column
            logger.info(f"Adding nights_str column for folder {folder}")
            df['night_str'] = df.apply(lambda x: add_night_column(x['hour'], x['weekday']), axis=1)

            # Plotting night evolution
            if PLOT_NIGHT_EVOLUTION:
                logger.info(f"Plotting night evolution for folder {folder}")
                plot_night_evolution(df, folder_output_dir, logger, laeq_column=slm_dict["LAEQ_COLUMN"], plotname=folder, indicador_noche="Ln")
            
            # Plotting night evolution 15 min
            if PLOT_NIGHT_EVOLUTION_15_MIN:
                logger.info(f"Plotting night evolution 15 min for folder {folder}")
                plot_night_evolution_15_min(df, folder_output_dir, logger, name_extension="15_min", laeq_column=slm_dict["LAEQ_COLUMN"], plotname=folder, indicador_noche="Ln")
            
        except Exception as e:
            logger.error(f"An error occurred while processing folder {folder}: {e}")
            


# def arg_parser():
#     parser = argparse.ArgumentParser(description='Plotting AudioMoth data')
#     parser.add_argument('-f', '--path_sonometers', type=str, required=False, help='Path to sonometers folder')
#     parser.add_argument('-a', '--agg_period', type=int, required=False, default=900, help='Aggregation period in seconds')
#     parser.add_argument('-o', '--output-dir', type=str, required=False, help='Output directory, if not provided, the output directory is the same as the input directory')
#     parser.add_argument('-p', '--percentiles', type=float, nargs='+', required=False, default=[90, 10], help='Percentiles to plot (L90 and L10 as default)')
#     return parser.parse_args()



# def main():
#     logger = setup_logging()
#     args = arg_parser()
    
#     # Enter the path to the sonometers folder
#     if args.path_sonometers:
#         input_folder = args.path_sonometers
#     else:
#         raise ValueError("Path to sonometers folder not provided")

#     # Enter the aggregation period in seconds, default is 900 seconds (15 minutes)
#     if args.agg_period:
#         PERIODO_AGREGACION = args.agg_period
#     else:
#         PERIODO_AGREGACION = config.PERIODO_AGREGACION
    
#     # Enter the percentiles to plot, default is [90, 10], they are L1, L5, L10, L50, L90
#     if args.percentiles:
#         PERCENTILES = args.percentiles
    
#     # Enter the output directory
#     clase_registro = os.path.basename(input_folder)
#     # if class is not provided, use the name of the parent folder
#     if clase_registro == '':
#         clase_registro = os.path.basename(os.path.dirname(input_folder))
    
#     try:
#         # Get the folders in the input folder
#         folders = [folder for folder in os.listdir(input_folder) if os.path.isdir(os.path.join(input_folder, folder))]
#         logger.info(f"Found folders: {folders}")
        
#         # Process all the folders
#         process_all_folders(input_folder, folders, PERIODO_AGREGACION, PERCENTILES, logger)
        
#         logger.info("Finished sonometer test script")

#     except Exception as e:
#         logger.exception(f"Error occurred: {e}")
        
        
# if __name__ == "__main__":
#     main()