import pandas as pd
import matplotlib.pyplot as plt
import os
plt.style.use("bmh")
from visualization import *
from reading import *
from utils import *
from config import *
from tqdm import tqdm
import glob



def load_data(file_path, logger):
    slm_type_function_mapping = {
        "814": (get_data_814, larson814_dict),
        "824": (get_data_824, larson824_dict),
        "lx_ES": (get_data_lx_ES, larsonlx_dict),
        "lx_EN": (get_data_lx_EN, larsonlx_dict),
        "SV307": (get_data_SV307, sv307_dict),
        "cesva": (get_data_cesva, cesva_dict),
        "sono-bilbo": (get_data_bilbo, sonometer_bilbo_dict),
        "audio-post": (get_data_audio, audiopost_dict),
    } # SLM stands for Sound Level Meter
    logger.info(f"Analizing {file_path}")

    # load the data for each SLM type until one works |  for each slm_type, (func, slm_dict) in slm_type_function_mapping.items(): means that for each key and value in the dictionary, the key is slm_type and the value is a tuple with the function and the dictionary | the function is the function to load the data and the dictionary is the dictionary with the column names for the SLM type
    for slm_type, (func, slm_dict) in slm_type_function_mapping.items():
        try:
            logger.info(f"Loading data for SLM type {slm_type}")
            df = func(file_path)
            logger.info(f"Data loaded for SLM type {slm_type}")
            return df, slm_type, slm_dict
        
        except Exception as e:
            clean_message = str(e).replace('\n', ' ')
            logger.warning(f"Failed to load data for SLM type {slm_type}: {clean_message}. Trying next SLM type")
            continue
    raise ValueError("SLM type not found or file could not be loaded")



def process_folder(folder_path, logger):
    logger.info(f"Processing folder {folder_path}")
    # folder contains a CESVA folder
    cesva_path = os.path.join(folder_path, 'CESVA')
    if os.path.isdir(cesva_path):
        # load the data from the CESVA folder
        subfolders = [f for f in os.listdir(cesva_path) if os.path.isdir(os.path.join(cesva_path, f))]
        
        # CESVA folder contains subfolders
        for subfolder in subfolders:
            #load the data from the first subfolder
            subfolder_path = os.path.join(cesva_path, subfolder)
            
            # subfolder contains measurement files
            files = [os.path.join(subfolder_path, f) for f in os.listdir(subfolder_path) if f.endswith(('.csv', '.xlsx', '.CSV', 'XLSX'))]
            if files:
                logger.info(f"Files found: {files}")
                return load_data(files[0], logger)  
            else:
                logger.warning(f"No measurement files found in {subfolder_path}")

    else:
        files = [os.path.join(folder_path, f) for f in os.listdir(folder_path) if f.endswith(('.csv', '.xlsx', '.CSV'))]
        logger.info(f"Files found: {files}")
        
        if not files:
            logger.warning(f"No measurement files found in {folder_path}")
            return None, None, None
        
        logger.info(f"Loading data from {files}")
        return load_data(files[0], logger) 
    return None, None, None 


def process_all_folders(input_folder, folders, PERIODO_AGREGACION, PERCENTILES, yamnet_csv, sufix_string, folder_coefficients, logger):
    print()
    for folder in tqdm(folders, desc="Processing folders"):
        reg_folder = os.path.join(input_folder, folder) # \\192.168.205.117\AAC_Server\INDUSTRIA\23132-IRUÑA_OCA_CANTERA\5-Resultados\FAA205-P1_CAMPAÑA1\SPL

        folder = folder.split("\\")[:-1]
        folder = os.path.join('\\\\', *folder)
        logger.info(f"\nEntering folder: {folder}")
        
        spl_string = "SPL"
        graphics_string = f"Graphics_{sufix_string}"

        logger.info(f"folder {folder}")
        result_dir_name = "5-Resultados"
        
        resultados_dir = reg_folder.split("\\")[:-3]
        logger.info(f"resultados_dir: {resultados_dir}")

        # join the path
        resultados_dir = os.path.join('\\\\', *resultados_dir, result_dir_name)
        logger.info(f"resultados_dir: {resultados_dir}") # \\192.168.205.117\AAC_Server\INDUSTRIA\23132-IRUÑA_OCA_CANTERA\5-Resultados

        if not os.path.exists(resultados_dir):
            os.makedirs(resultados_dir)
            logger.info(f"Created output folder: {resultados_dir}")
        
        folder_output_dir = os.path.join(resultados_dir, folder, spl_string, graphics_string)
        logger.info(f"folder_output_dir: {folder_output_dir}")
        if '3-Medidas' in folder_output_dir:
            folder_output_dir = folder_output_dir.replace('3-Medidas', '5-Resultados')

        if not os.path.exists(folder_output_dir):
            os.makedirs(folder_output_dir)
            logger.info(f"Created output folder: {folder_output_dir}")
            
        ##### trying to get the prediction file for each folder #####
        predictions_folder = os.path.join(resultados_dir, folder, "URBAN_Model", "Predictions")
        if '3-Medidas' in predictions_folder:
            predictions_folder = predictions_folder.replace('3-Medidas', '5-Resultados')
        if os.path.exists(predictions_folder):
            # list csv files in the directory
            predictions_files = glob.glob(os.path.join(predictions_folder, "*.csv"))
            if predictions_files:
                prediction_file = predictions_files[0]
                prediction_csv_file = prediction_csv(prediction_file)
            else:
                logger.info("No CSV files found in the predictions folder.")

        try:
            logger.info(f"\nProcessing folder {folder}") 
            df, slm_type, slm_dict = process_folder(reg_folder, logger)
            if df is None:
                logger.info(f"df is None")
                continue
            
            # add datetime columns, sort by datetime and set datetime as index
            df = add_datetime_columns(df, date_col='datetime') 
            df = df.sort_values('datetime')
            df.set_index('datetime', inplace=True)
            start_date = df.index[0]
            end_date = df.index[-1]
            logger.info(f"df was sorted by datetime and datetime was set as index")
            
            try:
                # drop the beginning and ending of the measurement (15min)
                df = df.loc[start_date + pd.Timedelta(REMOVE_START_TIME, unit='seconds'):end_date - pd.Timedelta(REMOVE_END_TIME, unit='seconds')]
                logger.info(f"df was trimmed, {REMOVE_START_TIME} secs from the beggining and {REMOVE_END_TIME} secs from the end")

                # add indicators column
                df['indicador_str'] = df.apply(lambda x: evaluation_period_str(x['hour']), axis=1)
                # add nights column
                df['night_str'] = df.apply(lambda x: add_night_column(x['hour'], x['weekday']), axis=1)
                logger.info(f"Adding nights_str column for folder {folder}")
                
                #df['oca'] = df.apply(lambda x: db_limit(x['hour'],ld_limit= LIMITE_DIA , le_limit= LIMITE_TARDE ,ln_limit= LIMITE_NOCHE) , axis=1)

                for key, value in folder_coefficients.items():
                    if '3-Medidas' in key and not 'SONOMETRO' in key:
                        key = key.replace('3-Medidas', '5-Resultados')
                    
                    key = key.split("\\")[:-1]
                    key = os.path.join('\\\\', *key)

                    # assign the value to the folder
                    if folder == key:
                        df = apply_db_correction(df, value)
                        logger.info(f"Apply {value} correction coefficient to the folder {folder}")
            except:
                logger.error(f"An error occurred while trimming the dataframe")
                continue

            logger.info(f"\nEntering the plotting section")
            folder = folder.split("\\")[-1]
            
            # add slm_dict column LAEQ_COLUMN_COEFF: with the value of LA_corrected
            slm_dict["LAEQ_COLUMN_COEFF"] = 'LA_corrected'
            slm_dict["LAMAX_COLUMN_COEFF"] = 'LAmax_corrected'
            slm_dict["LAMIN_COLUMN_COEFF"] = 'LAmin_corrected'

            # Plotting night evolution
            if PLOT_NIGHT_EVOLUTION:
                logger.info(f"[1] Plotting night evolution for folder {folder}")
                # plot_night_evolution(df, folder_output_dir, logger, laeq_column=slm_dict["LAEQ_COLUMN"], plotname=folder, indicador_noche="Ln")
                plot_night_evolution(df, folder_output_dir, logger, laeq_column=slm_dict["LAEQ_COLUMN_COEFF"], plotname=folder, indicador_noche="Ln")
            
            
            # Plotting night evolution 15 min
            if PLOT_NIGHT_EVOLUTION_15_MIN:
                logger.info(f"[2] Plotting night evolution 15 min for folder {folder}")
                # plot_night_evolution_15_min(df, folder_output_dir, logger, name_extension="15_min", laeq_column=slm_dict["LAEQ_COLUMN"], plotname=folder, indicador_noche="Ln")
                plot_night_evolution_15_min(df, folder_output_dir, logger, name_extension="15_min", laeq_column=slm_dict["LAEQ_COLUMN_COEFF"], plotname=folder, indicador_noche="Ln")


            # Plotting LEq power average with predictions
            if PLOT_PREDIC_LAEQ_15_MIN:
                logger.info(f"[3] Plotting PLOT_PREDIC_LAEQ for folder {folder}")
                # plot_predic_laeq_15_min(df, yamnet_csv, prediction_csv_file, folder_output_dir, logger, columns_dict=slm_dict, agg_period=PERIODO_AGREGACION, plotname=folder)
                plot_predic_laeq_15_min(df, yamnet_csv, prediction_csv_file, folder_output_dir, logger, columns_dict=slm_dict, agg_period=PERIODO_AGREGACION, plotname=folder)

            
            # Plotting time plot
            if PLOT_MAKE_TIME_PLOT:
                logger.info(f"[4] Plotting time plot for folder {folder}")
                make_time_plot(df, folder_output_dir, logger, columns_dict=slm_dict, agg_period=PERIODO_AGREGACION, plotname=folder, percentiles=PERCENTILES)
            

            # Plotting heatmap evolution hour
            if PLOT_HEATMAP_EVOLUTION_HOUR:
                logger.info(f"[5] Plotting heatmap for folder {folder}")
                plot_heatmap_evolution_hour(df, folder_output_dir, logger, values_column=slm_dict['LAEQ_COLUMN_COEFF'], agg_func=leq,plotname=folder)
            
            
            # Plotting heatmap evolution 15 min
            if PLOT_HEATMAP_EVOLUTION_15_MIN:
                logger.info(f"[6] Plotting heatmap 15 min for folder {folder}")
                plot_heatmap_evolution_15_min(df, folder_output_dir, logger, values_column=slm_dict['LAEQ_COLUMN_COEFF'], agg_func=leq,plotname=folder)
            

            # Plotting individual heatmap
            if PLOT_INDICADORES_HEATMAP:
                logger.info(f"[7] Plotting indicadores heatmap for folder {folder}")
                plot_indicadores_heatmap(df, folder_output_dir, logger, plotname=folder, ind_column=slm_dict["LAEQ_COLUMN_COEFF"])


            # Plotting day evolution
            if PLOT_DAY_EVOLUTION:
                logger.info(f"[8] Plotting day evolution for folder {folder}")
                plot_day_evolution(df, folder_output_dir, logger, laeq_column=slm_dict["LAEQ_COLUMN_COEFF"], plotname=folder)
            

            # Plotting period evolution
            if PLOT_PERIOD_EVOLUTION:
                logger.info(f"[9] Plotting period evolution (1) Ld (2) Le for folder {folder}")
                plot_period_evolution(df, folder_output_dir, logger, laeq_column=slm_dict["LAEQ_COLUMN_COEFF"], plotname=folder)
            

        except Exception as e:
            logger.error(f"An error occurred while processing folder {folder}: {e}")