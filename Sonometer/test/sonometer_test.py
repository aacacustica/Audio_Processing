import pandas as pd
import matplotlib.pyplot as plt
import os
plt.style.use("bmh")
from utils_sonometer_test import *
from config import *
from logging_config import setup_logging

def load_data(file_path):
    logger.info(f"Loading data from {file_path}...")
    slm_type_function_mapping = {
        "814": (get_data_814, larson814_dict),
        "824": (get_data_824, larson824_dict),
        "lx_ES": (get_data_lx_ES, larsonlx_dict),
        "lx_EN": (get_data_lx_EN, larsonlx_dict),
        "SV307": (get_data_SV307, SV307_dict),
        "cesva": (get_data_cesva, cesva_dict),
        "audio-post": (get_data_audio, audiopost_dict)
    }
    
    for slm_type, (func, slm_dict) in slm_type_function_mapping.items():
        try:
            df = func(file_path)
            logger.info(f"SLM type: {slm_type}")
            return df, slm_type, slm_dict
        except Exception as e:
            logger.error(f"Failed to load data for SLM type {slm_type}: {e}")
            continue

    raise ValueError("SLM type not found or file could not be loaded")

# process a single folder
def process_folder(folder_path):
    # if a folder named "CESVA" exists inside the folder_path
    cesva_path = os.path.join(folder_path, "CESVA")
    if os.path.isdir(cesva_path):
        logger.info(f"CESVA folder found, processing: {cesva_path}")
        # list all the subfolders inside the CESVA folder
        subfolders = [os.path.join(cesva_path, folder) for folder in os.listdir(cesva_path) if os.path.isdir(os.path.join(cesva_path, folder))]
        logger.info(f"Subfolders in CESVA: {subfolders}")
        # process each subfolder to find files
        for subfolder in subfolders:
            files = [os.path.join(subfolder, f) for f in os.listdir(subfolder) if f.endswith(('.csv', '.xlsx', '.CSV'))]
            logger.info(f"Files found in {subfolder}: {files}")
            if files:
                return load_data(files[0])
        logger.warning(f"No measurement files found in CESVA subfolders of {folder_path}")
    else:
        # process the folder directly if no CESVA subfolder
        files = [os.path.join(folder_path, f) for f in os.listdir(folder_path) if f.endswith(('.csv', '.xlsx', '.CSV'))]
        logger.info(f"Files found in {folder_path}: {files}")
        if files:
            return load_data(files[0])
        logger.warning(f"No measurement files found in {folder_path}")

    return None, None, None

# process all folders
def process_all_folders(folders):
    df_indicadores = pd.DataFrame()
    n_registro = []
    df_common_format = pd.DataFrame()

    for folder in folders:
        logger.info(f"\n\nProcessing folder: {folder}")
        reg_folder = os.path.join(CARPETA_MEDIDAS, folder)
            
        try:
            df, slm_type, slm_dict = process_folder(reg_folder)
            logger.info(f"SLM type: {slm_type}")
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
                make_timeplot(df, columns_dict=slm_dict, agg_period=PERIODO_AGREGACION, plotname=folder, percentiles=PERCENTILES)
            if PLOT_HEATMAP:
                plot_heatmap(df,values_column=slm_dict['LAEQ_COLUMN'], agg_func=leq,plotname=folder)
            if PLOT_DAY_EVOLUTION:
                plot_day_evolution(df,laeq_column=slm_dict["LAEQ_COLUMN"],plotname=folder)

            # add indicators column
            df['indicador_str'] = df.apply(lambda x: evaluation_period_str(x['hour']), axis=1)
                    
            if PLOT_PERIOD_EVOLUTION:
                plot_period_evolution(df, laeq_column=slm_dict["LAEQ_COLUMN"], plotname=folder)
            if PLOT_INDHEATMAP:
                plot_indheatmap(df, plotname=folder, ind_column=slm_dict["LAEQ_COLUMN"])


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
                plot_night_evolution(df,laeq_column=slm_dict["LAEQ_COLUMN"],plotname=folder)
            
            n_registro.append([folder for i in range(3)])
            
            # n_registro_valencia.append([folder for i in range(2)])
            
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

# Main execution block
if __name__ == "__main__":
    logger = setup_logging()
    logger.info("Starting sonometer test script...")

    # CARPETA_MEDIDAS = 
    clase_registro = os.path.basename(CARPETA_MEDIDAS)
    folders = [folder for folder in os.listdir(CARPETA_MEDIDAS) if os.path.isdir(os.path.join(CARPETA_MEDIDAS, folder))]

    df_indicadores, n_registro, df_common_format = process_all_folders(folders)

    flatten_list = [element for sublist in n_registro for element in sublist]
    logger.info(f'\nflatten_list {flatten_list}')
    
    # flatten_list_VALENCIA = [element for sublist in n_registro_valencia for element in sublist]
    # logger.info(f"Flatten list valencia: {flatten_list_VALENCIA}")
    

    ################ SAVE INDICADORES NORMALES ################
    df_indicadores["reg"] = flatten_list
    print(f'\nDataFrame with flatten list: {df_indicadores["reg"]}')

    df_indicadores.to_csv(f'indicadores_{clase_registro}.csv')
    # print(f'\nflatten_list {df_indicadores.to_csv(f'indicadores_{clase_registro}.csv')}')
    #df_common_format.to_csv(f'df_{clase_registro}.csv',index=False)

    ################ SAVE INDICADORES VALENCIA ################
    # df_indicadores_valencia["reg"] = flatten_list_VALENCIA
    # print(f'\nDataFrame with flatten list: {df_indicadores_valencia["reg"]}')

    # df_indicadores_valencia.to_csv('indicadores_valencia.csv')
    # print(f'\nflatten_list {df_indicadores_valencia.to_csv('indicadores_valencia.csv')}')

    logger.info("Finished sonometer test script")