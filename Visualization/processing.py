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
import json




def load_data(files, logger, new_date=None, new_time=None, new_threshold_date=None, new_threshold_time=None):
    slm_type_function_mapping = {
        "audiomoth": (get_data_audiomoth, audiopost_dict),
        "814": (get_data_814, larson814_dict),
        "824": (get_data_824, larson824_dict),
        "lx_ES": (get_data_lx_ES, larsonlx_dict),
        "lx_EN": (get_data_lx_EN, larsonlx_dict),
        "cesva": (get_data_cesva, cesva_dict),
        "SV307": (get_data_SV307, sv307_dict),
        "sono-bilbo": (get_data_bilbo, sonometer_bilbo_dict),
        "bruel&kjaer": (get_data_bruel_kjaer, bruel_kjaer_dict),
    } # SLM stands for Sound Level Meter
    # load the data for each SLM type until one works |  for each slm_type, (func, slm_dict) in slm_type_function_mapping.items(): means that for each key and value in the dictionary, the key is slm_type and the value is a tuple with the function and the dictionary | the function is the function to load the data and the dictionary is the dictionary with the column names for the SLM type
    file_path = files[0]
    for slm_type, (func, slm_dict) in slm_type_function_mapping.items():
        try:
            logger.info(f"Loading file {file_path} for SLM type {slm_type}")

            # this is the actual invocation of the function
            first_df = func(file_path, logger, new_date=new_date, new_time=new_time, new_threshold_date=new_threshold_date, new_threshold_time=new_threshold_time)

            # loggers
            if len(files) > 1 :
                dfs = [first_df]
                for file in files[1:]:
                    df_i = func(file, logger, new_date=new_date, new_time=new_time, new_threshold_date=new_threshold_date, new_threshold_time=new_threshold_time)
                    dfs.append(df_i)

                df = pd.concat(dfs,ignore_index=True)
                return df,slm_type,slm_dict
            else:
                
                logger.info("\n")
                logger.info(f"Data loaded for SLM type {slm_type}")
                return first_df, slm_type, slm_dict

        
        except Exception as e:
            clean_message = str(e).replace('\n', ' ')
            logger.warning(f"Failed to load data for SLM type {slm_type}: {clean_message}. Trying next SLM type")
            continue
    
    raise ValueError("SLM type not found or file could not be loaded")



def process_folder(folder_path, folder_date_time, folder_threshold, logger):

    cesva_path = os.path.join(folder_path, 'CESVA')
    
    if os.path.isdir(cesva_path):

        subfolders                              = [f for f in os.listdir(cesva_path) if os.path.isdir(os.path.join(cesva_path, f))]
        new_date, new_time                      = folder_date_time.get(folder_path, (None, None))
        new_threshold_date, new_threshold_time  = folder_threshold.get(folder_path, (None, None))
        
        for subfolder in subfolders:

            subfolder_path = os.path.join(cesva_path, subfolder)
            files = [os.path.join(subfolder_path, f) for f in os.listdir(subfolder_path) if f.endswith(('.csv', '.xlsx', '.CSV', 'XLSX'))]

            if files == []: files = [os.path.join(subfolder_path,'AI_MODEL','Predictions',f) for f in os.listdir(os.path.join(subfolder_path,'AI_MODEL','Predictions')) if f.endswith('.csv', '.xlsx', '.CSV', 'XLSX')]
            if files:
                return load_data(
                    files               = files, 
                    logger              = logger, 
                    new_date            = new_date, 
                    new_time            = new_time, 
                    new_threshold_date  = new_threshold_date, 
                    new_threshold_time  = new_threshold_time
                    )

    else:
        
        new_date, new_time                      = folder_date_time.get(folder_path, (None, None))
        new_threshold_date, new_threshold_time  = folder_threshold.get(folder_path, (None, None)) 
        files = [os.path.join(folder_path, f) for f in os.listdir(folder_path) if f.endswith(('.csv', '.xlsx', '.CSV'))]

        if files == []:files = [f for f in os.listdir(folder_path) if f.endswith('.csv')]                
        if not files: return None, None, None

        if files: 
            return load_data(
                files               = files, 
                logger              = logger, 
                new_date            = new_date, 
                new_time            = new_time, 
                new_threshold_date  = new_threshold_date, 
                new_threshold_time  = new_threshold_time)
    
    return None, None, None 


def process_all_folders(input_folder,filter_point, folders, PERIODO_AGREGACION, PERCENTILES, taxonomy, yamnet_csv, sufix_string, folder_coefficients, folder_date_time, folder_threshold, oca_limits, oca_type, logger):
    
    stable_version = get_stable_version(logger)

    agg_period = int(PERIODO_AGREGACION)
    
    if agg_period <=0: raise ValueError("PERIODO_AGREGACION debe ser mayor que cero")
    

    for folder in tqdm(folders, desc="Processing folders"): 

        prediction_csv_file                 = None
        df                                  = None
        slm_type                            = None
        slm_dict                            = None

        result_dir_name                     = "5-Resultados"
        spl_string                          = "SPL"
        graphics_string                     = f"Graphics_{sufix_string}"

        data_registers_folder               = os.path.join(input_folder, folder) 
        data_registers_folder               = data_registers_folder.replace("5-Resultados","3-Medidas")
        point_name                          = data_registers_folder.split("\\")[-2]

        if "\\" in data_registers_folder: 
            resultados_dir              = data_registers_folder.split("\\")[:-3]
            resultados_dir              = os.path.join('\\\\', *resultados_dir, result_dir_name)
        else: 
            resultados_dir              = data_registers_folder.split("/")[:-3]
            resultados_dir              = os.path.join(*resultados_dir,result_dir_name)    

        folder_output_dir                   = os.path.join(data_registers_folder,spl_string, graphics_string)
        predictions_folder                  = os.path.join(resultados_dir,point_name,"AI_MODEL","Predictions")
        predictions_files                   = glob.glob(os.path.join(predictions_folder, "*.csv"))
        predictions_visualization_folder    = predictions_folder.replace("Predictions", "Visualizations")
       
        if not os.path.exists(resultados_dir):
            os.makedirs(resultados_dir)
            logger.info(f"Created output folder: {resultados_dir}")

        if '3-Medidas' in folder_output_dir: folder_output_dir = folder_output_dir.replace('3-Medidas', '5-Resultados')

        if not os.path.exists(folder_output_dir): os.makedirs(folder_output_dir)

        if "\\" in folder:  folder = folder.split("\\")[-1]
        else: folder = folder.split("/")[-1]
            

        if not os.path.exists(predictions_folder): logger.warning(f"Predictions folder not found: {predictions_folder}")
            

        else: logger.warning("No CSV files found in the predictions folder.")
            
                
        
        if not os.path.exists(predictions_visualization_folder): os.makedirs(predictions_visualization_folder)

        logger.info(f"Nombre del punto:                     {point_name}")
        logger.info(f"Carpeta actual:                       {folder}")
        logger.info(f"Fichero de registros acusticos:       {data_registers_folder}")
        logger.info(f"Fichero de predicciones:              {predictions_folder}") 

        logger.info(f"Carpeta de salida:                    {folder_output_dir}")
        logger.info(f"Carpeta de salida de predicciones:    {predictions_visualization_folder}")
        logger.info(f"Carpeta de resultados:                {resultados_dir}")    
        logger.info(f"Graficando con periodo de agregación: {agg_period}\n")  

        ####################################################################
        # add datetime columns, sort by datetime and set datetime as index #
        ####################################################################

        logger.info(f"FOR SPL FILE: Añadiendo columna temporal, ordenando por esta y poniendola como índice de la tabla\n")

        try:

            if os.path.exists(data_registers_folder): df, slm_type, slm_dict = process_folder(data_registers_folder, folder_date_time, folder_threshold, logger)
            if os.path.exists(predictions_folder) and predictions_files: prediction_csv_file = prediction_csv(predictions_files[0])

            if df is None: 
                logger.warning(f"No se encontraron datos SPL en {data_registers_folder}")
                continue
            if prediction_csv_file is None:
                logger.warning(f"No se encontraron datos PRED en {predictions_files[0]}")

            if TENERIFE_TIMEZONE: 
                timezone_offset = pd.Timedelta(hours=1)
                df['datetime']                      = pd.to_datetime(df['datetime'],errors = 'coerce') - timezone_offset
                prediction_csv_file['date']         = (pd.to_datetime(prediction_csv_file['date'],errors = 'coerce') - timezone_offset)


            if df is not None:
                df = add_datetime_columns(df,logger, date_col='datetime')
                df = df.sort_values('datetime')
                df.set_index('datetime', inplace=True, drop=False)
                start_date = df.index[0]
                end_date = df.index[-1]

            else:
                logger.warning(f"SPL file is None")
                continue

            logger.info(f"FOR PREDICTION FILE: Añadiendo columna temporal, ordenando por esta y poniendola como índice de la tabla")

            if prediction_csv_file is not None:
                
                prediction_csv_file = add_datetime_columns_pred(prediction_csv_file, logger, date_col='date')
                prediction_csv_file = prediction_csv_file.sort_values('date')
                prediction_csv_file.set_index('date', inplace=True, drop=False)
                pred_start_date = prediction_csv_file.index[0]
                pred_end_date = prediction_csv_file.index[-1]

            else: 
                logger.warning(f"prediction_csv_file is None")
                continue

            logger.info(f"")
            logger.info(f"SPL fecha de inicio:  {start_date}.")
            logger.info(f"SPL fecha de fin:     {end_date}.")
            logger.info(f"PRED  start date      {pred_start_date}.")
            logger.info(f"PRED fecha de fin:    {pred_end_date}.")
            logger.info(f"")

        except Exception as e:
            logger.warning(f"Error desconocido al añadir la columna temporal: {e}")    
            continue


        ####################################################################
        # drop the beginning and ending of the measurement (15min)         #
        ####################################################################
            
        logger.info(f"SPL: Borrando {REMOVE_START_TIME} del principio de la tabla y {REMOVE_END_TIME} del final de la tabla ...")
        logger.info(f"PRED: Borrando {REMOVE_START_TIME} del principio de la tabla y {REMOVE_END_TIME} del final de la tabla ...\n")

        try:

            df = trim_dataframe(
                dataframe                   = df,
                start_timestamp             = start_date,
                end_timestamp               = end_date,
                requested_start_seconds     = REMOVE_START_TIME,
                requested_end_seconds       = REMOVE_END_TIME,
                logger                      = logger,
                dataframe_name              = "SPL df",
                max_trim_fraction           = 0.10
            )

            prediction_csv_file = trim_dataframe(
                dataframe                   = prediction_csv_file,
                start_timestamp             = pred_start_date,
                end_timestamp               = pred_end_date,
                requested_start_seconds     = REMOVE_START_TIME,
                requested_end_seconds       = REMOVE_END_TIME,
                logger                      = logger,
                dataframe_name              = "Prediction df",
                max_trim_fraction           = 0.10
            )

            if df is None or df.empty:
                logger.warning(f"El dataframe de datos acusticos quedó vacío tras el recorte")
                continue

            if prediction_csv_file is None or prediction_csv_file.empty: 
                logger.warning(f"El dataframe de datos de predicciones quedó vacío tras el recorte")
                continue

            df['indicador_str']                     = df['hour'].apply(evaluation_period_str)
            prediction_csv_file['indicador_str']    = prediction_csv_file['hour'].apply( evaluation_period_str )

            logger.info(f"SPL: Eliminado {REMOVE_START_TIME} del principio de la tabla y {REMOVE_END_TIME} del final.")
            logger.info(f"SPL: Formato de la tabla tras ajuste temporal: {df.shape}.")
            logger.info(f"PRED: Eliminado {REMOVE_START_TIME} del principio de la tabla y {REMOVE_END_TIME} del final.")
            logger.info(f"PRED: Formato de la tabla tras ajuste temporal: {prediction_csv_file.shape}.\n")
            
        except Exception as e:
            logger.error(f"Ha ocurrido un error recortando el dataframe {REMOVE_START_TIME} desde el principio y {REMOVE_END_TIME} desde el final: {e}")
            continue
                
            
    
        ####################################################################
        # Adding nights column                                             #
        ####################################################################

        logger.info(f"Añadiendo columna de noche en ambas tablas\n")

        try:

            df['night_str'] = df.apply( lambda x: add_night_column(x['hour'], x['weekday']), axis=1)
            if prediction_csv_file is not None: prediction_csv_file['night_str'] = prediction_csv_file.apply( lambda x: add_night_column(x['hour'], x['weekday']),axis=1)

            logger.info(f"SPL: Columna de noche añadida.")
            logger.info(f"PRED: Columna de noche añadida.\n")

        except Exception as e:
            logger.error(f"Ha ocurrido un error añadiendo la columna de datos de noche a los dataframes SPL y Predicciones: {e}")
            continue



        ####################################################################
        # Adding OCA column                                                #
        ####################################################################

        logger.info(f"Añadiendo columna OCA a ambas tablas\n")

        try:
            df['oca'] = df['hour'].apply( lambda h: db_limit(h, **oca_limits))

            if prediction_csv_file is not None:

                prediction_csv_file = prediction_csv_file.dropna(subset=["date",'class','probability'])
                if prediction_csv_file.empty: prediction_csv_file = None
                    
            if df.isnull().values.any(): logger.warning("There are nan values in the dataframe")  
            logger.info(f"SPL: Columna OCA añadida.")
            logger.info(f"PRED: Columna OCA añadida.\n")        

        except Exception as e:
            logger.error(f"Ha ocurrido un error añadiendo la columna OCA en los dataframes SPL y Predicciones: {e}")
            continue




        ####################################################################
        # Applying DB Correction to the data                               #
        ####################################################################

        logger.info(f"Aplicando corrección de decibelios en ambas tablas \n")
        
        try:

            tuple_folder_coeff = list(folder_coefficients.items())
            current_paths = {normalize_path(data_registers_folder),normalize_path(data_registers_folder.replace('3-Medidas','5-Resultados'))}
            matching_coefficients = [(configured_path,value) for configured_path,value in folder_coefficients.items() if normalize_path(configured_path) in current_paths]

            if not matching_coefficients: logger.warning("No existe un coeficiente configurado para %s",data_registers_folder)
            else:

                coefficient_values = {float(value) for _,value in matching_coefficients}
                if len(coefficient_values) >1: raise ValueError(f"Hay coeficientes diferentes configurados para la misma medida: {matching_coefficients}")
                coefficient = coefficient_values.pop()

                df = apply_db_correction(df,coefficient,logger)

                logger.info("Corrección de %.3f dB aplicada una vez a %s",coefficient,data_registers_folder)


        except Exception as e:
            logger.error(f"Ha ocurrido un error al aplicar la corrección de decibelios en los datos: {e}")            
            continue     


        if "\\" in folder: folder = folder.split("\\")[-1]
        else: folder = folder.split("/")[-1]

        ####################################################################
        # Plotting                                                         #
        ####################################################################          

        slm_dict["LAEQ_COLUMN_COEFF"] = 'LA_corrected'
        slm_dict["LAMAX_COLUMN_COEFF"] = 'LAmax_corrected'
        slm_dict["LAMIN_COLUMN_COEFF"] = 'LAmin_corrected'

        # Plotting night evolution
        if PLOT_NIGHT_EVOLUTION:
            logger.info(f"[1] Plotting night evolution for folder {folder}\n")
            plot_night_evolution(df, folder_output_dir, logger, laeq_column=slm_dict["LAEQ_COLUMN_COEFF"], plotname=folder, indicador_noche="Ln")
        
        # Plotting night evolution 15 min
        if PLOT_NIGHT_EVOLUTION_15_MIN:
            logger.info(f"\n[2] Plotting night evolution 15 min for folder {folder}\n")
            plot_night_evolution_15_min(df, folder_output_dir, logger, name_extension="15_min", laeq_column=slm_dict["LAEQ_COLUMN_COEFF"], plotname=folder, indicador_noche="Ln")


        # Plotting LEq power average with predictions
        if PLOT_PREDIC_LAEQ_15_MIN:
            logger.info(f"\n[3] Plotting PLOT_PREDIC_LAEQ for folder {folder}\n")
            plot_predic_laeq_15_min(df, yamnet_csv, taxonomy, prediction_csv_file, predictions_visualization_folder, logger, columns_dict=slm_dict, agg_period=agg_period, plotname=folder)

        
        if PLOT_PREDIC_LAEQ_15_MIN_PERIOD:
            logger.info(f"\n[4] Plotting PLOT_PREDIC_LAEQ_15_MIN_PERIOD for folder {folder}\n")
            plot_predic_laeq_15_min_period(df, yamnet_csv, taxonomy, prediction_csv_file, predictions_visualization_folder, logger, columns_dict=slm_dict, agg_period=agg_period, plotname=folder)


        if PLOT_PREDIC_LAEQ_15_MIN_4H:
            logger.info(f"\n[5] Plotting PLOT_PREDIC_LAEQ_4H for folder {folder}\n")
            plot_predic_laeq_15_min_4h(df, yamnet_csv,taxonomy, prediction_csv_file, predictions_visualization_folder, logger, columns_dict=slm_dict, agg_period=agg_period, plotname=folder)


        # Plotting stack bar with predictions class
        if PLOT_PREDICTION_STACK_BAR:
            logger.info(f"\n[6] Plotting PLOT_PREDICTION_STACK_BAR for folder {folder}\n")
            plot_prediction_stack_bar(prediction_csv_file, yamnet_csv, taxonomy, predictions_visualization_folder, logger, plotname=folder)
        

        # Plotting prediction map
        if PLOT_PREDICTION_MAP:
            logger.info(f"\n[7] Plotting PLOT_PREDICTION_MAP for folder {folder}\n")
            plot_prediction_map(prediction_csv_file, taxonomy,agg_period, predictions_visualization_folder, logger, plotname=folder)

        
        # Plotting tree map
        if PLOT_TREE_MAP:
            logger.info(f"\n[8] Plotting PLOT_TREE_MAP for folder {folder}\n")
            plot_tree_map(prediction_csv_file,taxonomy,predictions_visualization_folder, logger, plotname=folder)

        
        # Plotting time plot
        if PLOT_MAKE_TIME_PLOT:
            logger.info(f"[9] Plotting time plot for folder {folder}\n")
            make_time_plot(df, folder_output_dir, logger, columns_dict=slm_dict, agg_period=agg_period, plotname=folder, percentiles=PERCENTILES)


        # Plotting heatmap evolution hour
        if PLOT_HEATMAP_EVOLUTION_HOUR:
            logger.info(f"\n[10] Plotting heatmap for folder {folder}\n")
            plot_heatmap_evolution_hour(df, folder_output_dir, logger, values_column=slm_dict['LAEQ_COLUMN_COEFF'], agg_func=leq,plotname=folder)
        
        
        # Plotting heatmap evolution 15 min
        if PLOT_HEATMAP_EVOLUTION_15_MIN:
            logger.info(f"\n[11] Plotting heatmap 15 min for folder {folder}\n")
            plot_heatmap_evolution_15_min(df, folder_output_dir, logger, values_column=slm_dict['LAEQ_COLUMN_COEFF'], agg_func=leq,plotname=folder)
        

        # Plotting individual heatmap
        if PLOT_INDICADORES_HEATMAP:
            logger.info(f"\n[12] Plotting indicadores heatmap for folder {folder}\n")
            plot_indicadores_heatmap(df, folder_output_dir, logger, plotname=folder, ind_column=slm_dict["LAEQ_COLUMN_COEFF"])


        # Plotting day evolution
        if PLOT_DAY_EVOLUTION:
            logger.info(f"\n[13] Plotting day evolution for folder {folder}\n")
            plot_day_evolution(df, folder_output_dir, logger, laeq_column=slm_dict["LAEQ_COLUMN_COEFF"], plotname=folder)
        

        # Plotting period evolution
        if PLOT_PERIOD_EVOLUTION:
            logger.info(f"\n[14] Plotting period evolution (1) Ld (2) Le for folder {folder}\n")
            plot_period_evolution(df, folder_output_dir, logger, laeq_column=slm_dict["LAEQ_COLUMN_COEFF"], plotname=folder)
        

        # I dont know why I commented this out
        if PLOT_SPECTROGRAM_1_3:
            logger.info(f"\n[15] Plotting spectrogram for folder {folder}\n")
            # plt_spectrogram(df_oct, folder_output_dir, logger, plotname=folder)
            plt_spectrogram(df, folder_output_dir, sufix_string, logger, plotname=folder)



        try:

            info_dict = {
                "PERIODO_AGREGACION":       PERIODO_AGREGACION,
                "PERCENTILES":              PERCENTILES,
                "folder_coeff":             tuple_folder_coeff,
                "stable_version":           stable_version,
                "slm_type":                 slm_type,
                "oca_limits":               oca_limits,
                "oca_type":                 oca_type,
                "tenerife_timezone":        TENERIFE_TIMEZONE,
            }
        
            with open(os.path.join(folder_output_dir, "processing_parameters.json"), 'w') as f: json.dump(info_dict, f)
            logger.info(f"Saved processing_parameters.json in {folder_output_dir}\n")
        except Exception as e:
            logger.error(f"Ha ocurrido un error al crear y guardar el fichero resumen: {e}")