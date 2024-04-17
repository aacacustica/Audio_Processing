import pandas as pd
import matplotlib.pyplot as plt
import os
plt.style.use("bmh")
from sound_data_visualization import *
from sound_data_reader import *
from time_level_utils import *
from config import *
from tqdm import tqdm
from config import *
import glob



def load_data(file_path, logger):
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
    # load the data for each SLM type until one works |  for each slm_type, (func, slm_dict) in slm_type_function_mapping.items(): means that for each key and value in the dictionary, the key is slm_type and the value is a tuple with the function and the dictionary | the function is the function to load the data and the dictionary is the dictionary with the column names for the SLM type
    for slm_type, (func, slm_dict) in slm_type_function_mapping.items():
        try:
            logger.info(f"Loading data for SLM type {slm_type}")
            df = func(file_path)
            return df, slm_type, slm_dict
        
        except Exception as e:
            clean_message = str(e).replace('\n', ' ')
            logger.warning(f"Failed to load data for SLM type {slm_type}: {clean_message}. Trying next SLM type")
            continue
    raise ValueError("SLM type not found or file could not be loaded")



def process_folder(folder_path, logger):
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


def process_all_folders(input_folder, folders, PERIODO_AGREGACION, PERCENTILES, yamnet_csv, sufix_string, correction_coefficient, logger):
    for folder in tqdm(folders, desc="Processing folders"):
        logger.info(f"\nEntering folder: {folder}")
        
        if folder in correction_coefficient:
            current_coefficient = correction_coefficient[folder]
            logger.info(f"Using correction coefficient {current_coefficient} for {folder}")
        else:
            logger.warning(f"No correction coefficient found for {folder}. Using default of 1.")
            current_coefficient = 0
        
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
            logger.info(f"df was loaded successfully")
            
            # applying the correction to the laeq column
            logger.info(f"Applying correction to the laeq column with coefficient {current_coefficient}")
            df = apply_db_correction(df, current_coefficient, slm_dict["LAEQ_COLUMN"], slm_dict["LAMAX_COLUMN"], slm_dict["LAMIN_COLUMN"])
            
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

                # add corrected columns to slm_dict
                slm_dict['LA_corrected'] = 'LA_corrected'
                slm_dict['LAmax_corrected'] = 'LAmax_corrected'
                slm_dict['LAmin_corrected'] = 'LAmin_corrected'
            except:
                logger.error(f"An error occurred while trimming the dataframe")
                continue

            logger.info(f"\nEntering the plotting section")
            folder = folder.split("\\")[-1]

            # Plotting night evolution
            if PLOT_NIGHT_EVOLUTION:
                logger.info(f"[1] Plotting night evolution for folder {folder}")
                # plot_night_evolution(df, folder_output_dir, logger, laeq_column=slm_dict["LAEQ_COLUMN"], plotname=folder, indicador_noche="Ln")
                plot_night_evolution(df, folder_output_dir, logger, laeq_column=df['LA_corrected'], plotname=folder, indicador_noche="Ln")
            

            # Plotting night evolution 15 min
            if PLOT_NIGHT_EVOLUTION_15_MIN:
                logger.info(f"[2] Plotting night evolution 15 min for folder {folder}")
                plot_night_evolution_15_min(df, folder_output_dir, logger, name_extension="15_min", laeq_column=slm_dict["LA_corrected"], plotname=folder, indicador_noche="Ln")
                # plot_night_evolution_15_min(df, folder_output_dir, logger, name_extension="15_min", laeq_column=df['LA_corrected'], plotname=folder, indicador_noche="Ln")


            # Plotting LEq power average with predictions
            if PLOT_PREDIC_LAEQ_15_MIN:
                logger.info(f"[3] Plotting PLOT_PREDIC_LAEQ for folder {folder}")
                plot_predic_laeq_15_min(df, yamnet_csv, prediction_csv_file, folder_output_dir, logger, columns_dict=slm_dict, agg_period=PERIODO_AGREGACION, plotname=folder)


             # Plotting LEq power average with predictions
            if PLOT_PREDIC_LAEQ_15_MIN_Lx:
                logger.info(f"[3] Plotting PLOT_PREDIC_LAEQ for folder {folder}")
                plot_predic_laeq_15_min_Lx(df, yamnet_csv, prediction_csv_file, folder_output_dir, logger, columns_dict=slm_dict, agg_period=PERIODO_AGREGACION, plotname=folder)


            # Plotting time plot
            if PLOT_MAKE_TIME_PLOT:
                logger.info(f"[4] Plotting time plot for folder {folder}")
                make_time_plot(df, folder_output_dir, logger, columns_dict=slm_dict, agg_period=PERIODO_AGREGACION, plotname=folder, percentiles=PERCENTILES)
            

            # Plotting heatmap evolution hour
            if PLOT_HEATMAP_EVOLUTION_HOUR:
                logger.info(f"[5] Plotting heatmap for folder {folder}")
                # plot_heatmap_evolution_hour(df, folder_output_dir, logger, values_column=slm_dict['LAEQ_COLUMN'], agg_func=leq,plotname=folder)
                plot_heatmap_evolution_hour(df, folder_output_dir, logger, values_column=slm_dict['LA_corrected'], agg_func=leq,plotname=folder)
            

            # Plotting heatmap evolution 15 min
            if PLOT_HEATMAP_EVOLUTION_15_MIN:
                logger.info(f"[6] Plotting heatmap 15 min for folder {folder}")
                # plot_heatmap_evolution_15_min(df, folder_output_dir, logger, values_column=slm_dict['LAEQ_COLUMN'], agg_func=leq,plotname=folder)
                plot_heatmap_evolution_15_min(df, folder_output_dir, logger, values_column=slm_dict['LA_corrected'], agg_func=leq,plotname=folder)

            
            # Plotting individual heatmap
            if PLOT_INDICADORES_HEATMAP:
                logger.info(f"[9] Plotting indicadores heatmap for folder {folder}")
                # plot_indicadores_heatmap(df, folder_output_dir, logger, plotname=folder, ind_column=slm_dict["LAEQ_COLUMN"])
                plot_indicadores_heatmap(df, folder_output_dir, logger, plotname=folder, ind_column=slm_dict["LA_corrected"])


            # Plotting day evolution
            if PLOT_DAY_EVOLUTION:
                logger.info(f"[7] Plotting day evolution for folder {folder}")
                # plot_day_evolution(df, folder_output_dir, logger, laeq_column=slm_dict["LAEQ_COLUMN"], plotname=folder)
                plot_day_evolution(df, folder_output_dir, logger, laeq_column=slm_dict["LA_corrected"], plotname=folder)
            

            # Plotting period evolution
            # if PLOT_PERIOD_EVOLUTION:
            #     logger.info(f"[8] Plotting period evolution [Ld and Le] for folder {folder}")
            #     plot_period_evolution(df, folder_output_dir, logger, laeq_column=slm_dict["LA_corrected"], plotname=folder)

            if PLOT_LD_EVOLUTION:
                logger.info(f"[8] Plotting period evolution [Ld] for folder {folder}")
                plot_ld_evolution(df, folder_output_dir, logger, laeq_column=slm_dict["LA_corrected"], plotname=folder)
            
            if PLOT_LE_EVOLUTION:
                logger.info(f"[9] Plotting period evolution [Le] for folder {folder}")
                plot_le_evolution(df, folder_output_dir, logger, laeq_column=slm_dict["LA_corrected"], plotname=folder)
            


        except Exception as e:
            logger.error(f"An error occurred while processing folder {folder}: {e}")
