import pandas as pd
import matplotlib.pyplot as plt
import os
import argparse
plt.style.use("bmh")
from data_plotter import *
from data_reader import *
from utils_plotter import *
import config
from config import *
from logging_config import setup_logging
from tqdm import tqdm

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
    cesva_path = os.path.join(folder_path, 'CESVA')
    if os.path.isdir(cesva_path):
        subfolders = [f for f in os.listdir(cesva_path) if os.path.isdir(os.path.join(cesva_path, f))]
        for subfolder in subfolders:
            subfolder_path = os.path.join(cesva_path, subfolder)
            files = [os.path.join(subfolder_path, f) for f in os.listdir(subfolder_path) if f.endswith(('.csv', '.xlsx', '.CSV', 'XLSX'))]
            logger.info(f"Files found in {subfolder}: {files}")
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
    df_indicadores = pd.DataFrame()
    n_registro = []
    df_common_format = pd.DataFrame()

    for folder in tqdm(folders, desc="Processing folders"):
        logger.info(f"Processing folder: {folder}")
        reg_folder = os.path.join(input_folder, folder)

        folder_output_dir = os.path.join(reg_folder, "Results", "Sonometer_plots")
        os.makedirs(folder_output_dir, exist_ok=True)

        try:
            df, slm_type, slm_dict = process_folder(reg_folder, logger)
            if df is None:
                continue

            # add datetime columns
            df = add_datetime_columns(df, date_col='datetime') 
            df = df.sort_values('datetime')
            df.set_index('datetime', inplace=True)
            start_date = df.index[0]
            end_date = df.index[-1]
            
            # drop the beginning and ending of the measurement(15min)
            try:
                df = df.loc[start_date + pd.Timedelta(900, unit='seconds'):end_date - pd.Timedelta(900, unit='seconds')]
            except:
                pass

            #df['oca'] = df.apply(lambda x: db_limit(x['hour'],ld_limit= LIMITE_DIA , le_limit= LIMITE_TARDE ,ln_limit= LIMITE_NOCHE) , axis=1)
            #print(df)

            if PLOT_TIME:
                make_timeplot(df, folder_output_dir, logger, columns_dict=slm_dict, agg_period=PERIODO_AGREGACION, plotname=folder, percentiles=PERCENTILES)
            if PLOT_HEATMAP:
                plot_heatmap(df, folder_output_dir, logger, values_column=slm_dict['LAEQ_COLUMN'], agg_func=leq,plotname=folder)
            if PLOT_DAY_EVOLUTION:
                plot_day_evolution(df, folder_output_dir, logger, laeq_column=slm_dict["LAEQ_COLUMN"], plotname=folder)

            # add indicators column
            df['indicador_str'] = df.apply(lambda x: evaluation_period_str(x['hour']), axis=1)
                    
            if PLOT_PERIOD_EVOLUTION:
                plot_period_evolution(df, folder_output_dir, logger, laeq_column=slm_dict["LAEQ_COLUMN"], plotname=folder)
            if PLOT_INDHEATMAP:
                plot_indheatmap(df, folder_output_dir, logger, plotname=folder, ind_column=slm_dict["LAEQ_COLUMN"])

            ############### INDICADORES NORMALES ###############
            indicadores = get_day_levels(df, laeq_column=slm_dict['LAEQ_COLUMN'])
            df_indicadores = pd.concat([df_indicadores, indicadores])

            ################ INDICADORES VALENCIA ###############
            # indicadores_valencia = get_day_levels_valencia(df, laeq_column=slm_dict['LAEQ_COLUMN'])
            # df_indicadores_valencia = pd.concat([df_indicadores_valencia, indicadores_valencia])
            # df_indicadores_valencia.loc[df_indicadores_valencia['reg'].isnull(), 'reg'] = folder
            
            # add nights column
            df['night_str'] = df.apply(lambda x: add_night_column(x['hour'], x['weekday']), axis=1)

            if PLOT_NIGHT_EVOLUTION:
                plot_night_evolution(df, folder_output_dir, logger, laeq_column=slm_dict["LAEQ_COLUMN"], plotname=folder)
            if PLOT_NIGHT_EVOLUTION_15_MIN:
                plot_night_evolution_15_min(df, folder_output_dir, logger, name_extension="15_min", laeq_column=slm_dict["LAEQ_COLUMN"], plotname=folder)
            
            n_registro.append([folder for i in range(3)])
            
            # formato comun
            map_dict = {slm_dict['LAEQ_COLUMN']  : "LAeq",
                        slm_dict['LAMAX_COLUMN'] : "LAmax",
                        slm_dict['LAMIN_COLUMN'] :'LAmin'}
            
            df_temp = df.copy()
            df_temp = df_temp.reset_index()
            df_temp = df_temp.rename(columns=map_dict)
            df_temp["ubicacion"] = folder # nombre de las carpetas obligatorio referencia a ubicación de la medida
            df_temp["slm_type"] = slm_type
            df_temp = df_temp[common_columns]
            df_common_format = pd.concat([df_common_format,df_temp])
                
        except Exception as e:
            logger.error(f"An error occurred while processing folder {folder}: {e}")
    return df_indicadores, n_registro, df_common_format

def save_indicadores(df_indicadores, n_registro, input_folder, clase_registro, logger, df_indicadores_valencia=None, n_registro_valencia=None):
    flatten_list = [element for sublist in n_registro for element in sublist]
    df_indicadores["reg"] = flatten_list
    df_indicadores.to_csv(f'{input_folder}/indicadores_{clase_registro}.csv')
    logger.info(f"Saved normal indicators to {input_folder}/indicadores_{clase_registro}.csv")

    if df_indicadores_valencia is not None and n_registro_valencia is not None:
        flatten_list_valencia = [element for sublist in n_registro_valencia for element in sublist]
        df_indicadores_valencia["reg"] = flatten_list_valencia
        df_indicadores_valencia.to_csv(f'{input_folder}/indicadores_valencia_{clase_registro}.csv')
        logger.info(f"Saved Valencia indicators to {input_folder}/indicadores_valencia_{clase_registro}.csv")

def arg_parser():
    parser = argparse.ArgumentParser(description='Plotting AudioMoth data')
    parser.add_argument('-f', '--path_sonometers', type=str, required=False, help='Path to sonometers folder')
    parser.add_argument('-a', '--agg_period', type=int, required=False, default=900, help='Aggregation period in seconds')
    parser.add_argument('-o', '--output-dir', type=str, required=False, help='Output directory')
    parser.add_argument('-p', '--percentiles', type=float, nargs='+', required=False, default=[90, 10], help='Percentiles to plot (L90 and L10 as default)')
    return parser.parse_args()

def main():
    logger = setup_logging()
    args = arg_parser()
    
    if args.path_sonometers:
        input_folder = args.path_sonometers
    else:
        logger.error("Path to sonometers folder not provided")
        raise ValueError("Path to sonometers folder not provided")

    if args.agg_period:
        PERIODO_AGREGACION = args.agg_period
    else:
        PERIODO_AGREGACION = config.PERIODO_AGREGACION
    
    if args.percentiles:
        PERCENTILES = args.percentiles
        
    clase_registro = os.path.basename(input_folder)
    if clase_registro == '':
        clase_registro = os.path.basename(os.path.dirname(input_folder))
    
    try:     
        folders = [folder for folder in os.listdir(input_folder) if os.path.isdir(os.path.join(input_folder, folder))]
        logger.info(f"Found folders: {folders}")
        df_indicadores, n_registro, df_common_format = process_all_folders(input_folder, folders, PERIODO_AGREGACION, PERCENTILES, logger)
        logger.info(f"df_indicadores: {df_indicadores}")
        save_indicadores(df_indicadores, n_registro, input_folder, clase_registro, logger)
        # save_indicadores(df_indicadores, n_registro, input_folder, clase_registro, logger, df_indicadores_valencia, n_registro_valencia)
        # logger.info(f"df_common_format: {df_common_format}")
        logger.info("Finished sonometer test script")

    except Exception as e:
        logger.exception(f"Error occurred: {e}")
        
if __name__ == "__main__":
    main()