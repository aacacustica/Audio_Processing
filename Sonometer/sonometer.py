# ver 1
# Nov.23
# se elimina la representación INDHEATMAP, que pasa a utils_general y se desahabilita el cálculo de los indicadores de Valencia


from ntpath import join
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os
plt.style.use("bmh")
from utils_sonometer import *
from tqdm import tqdm
import time
from matplotlib.colors import ListedColormap


# parametros
# CARPETA_MEDIDAS = r'C:\Users\AAC-ASM\Desktop\bilbao' # formato oblgatorio para la carpeta de medidas -> REGISTROS_CONTINUOS_{nombre_expediente}
CARPETA_MEDIDAS = "/run/user/1000/gvfs/smb-share:server=192.168.205.117,share=aac_server/OCIO/MER_OCIO_BILBAO_2023"
CARPETA_MEDIDAS = os.path.normpath(CARPETA_MEDIDAS)

LIMITE_DIA = 65
LIMITE_NOCHE = 55
LIMITE_TARDE = 55
PERIODO_AGREGACION = 900 # SEGUNDOS
PERCENTILES = False
PLOT_TIME = True
PLOT_HEATMAP = True
PLOT_INDHEATMAP = True
PLOT_DAY_EVOLUTION = False
PLOT_PERIOD_EVOLUTION = True
PLOT_NIGHT_EVOLUTION = True

if  PERIODO_AGREGACION > 299:
    PERCENTILES = True

print(f'Current directory {os.getcwd()}\n')

# list mesaurement files
clase_registro = os.path.basename(CARPETA_MEDIDAS)
folders = [folder for folder in os.listdir(CARPETA_MEDIDAS) if os.path.isdir(os.path.join(CARPETA_MEDIDAS,folder))]
files = []
df_indicadores = pd.DataFrame()
# df_indicadores_valencia = pd.DataFrame()
n_registro = []
# n_registro_valencia = []
df_common_format = pd.DataFrame()

for folder in folders:
    print(f'\n\n ************** Folder working with: {folder} **************')
    
    reg_folder = os.path.join(CARPETA_MEDIDAS, folder)
    file = [os.path.join(reg_folder,f) for f in os.listdir(reg_folder) if f.endswith(('.csv','.xlsx','.CSV'))]
    
    slm_type = ""
    slm_dict = {}
    df = pd.DataFrame()
    figures_folder = os.path.join(reg_folder, "figures_{folder}")
    
    try:
        try:
            df = get_data_814(file[0])
            slm_type = "814"
            slm_dict = larson814_dict
            print(f"\nSLM type: {slm_type}\n")
        except Exception as e:
            pass

        try: 
            df = get_data_824(file[0])
            slm_type = "824"
            slm_dict = larson824_dict
            print(f"\nSLM type: {slm_type}\n")
        except Exception as e:
            pass

        try:
            df = get_data_lx_ES(file[0])
            slm_type = "lx_ES"
            slm_dict = larsonlx_dict
            print(f"\nSLM type: {slm_type}\n")
        except Exception as e:
            pass

        try:
            df = get_data_lx_EN(file[0])
            slm_type = "lx_EN"
            slm_dict = larsonlx_dict
            print(f"\nSLM type: {slm_type}\n")
        except Exception as e:
            pass

        try:
            df = get_data_SV307(file[0])
            slm_type = "SV307"
            slm_dict = SV307_dict 
            print(f"\nSLM type: {slm_type}\n")
        except Exception as e:
            pass

        try:
            df = get_data_cesva(reg_folder)
            slm_type = "cesva"
            slm_dict = cesva_dict 
            print(f"\nSLM type: {slm_type}\n")
        except Exception as e:
            pass

        try:
            df = get_data_audio(file[0])
            slm_type = "audio-post"
            slm_dict = audiopost_dict 
            print(f"\nSLM type: {slm_type}\n")
        except Exception as e:
            pass

        # add datetime columns
        df = add_datetime_columns(df, date_col='datetime') 
        df = df.sort_values('datetime')
        df.set_index('datetime', inplace=True)
        start_date = df.index[0]
        end_date = df.index[-1]
        
        duration = end_date - start_date
        
        print("Fecha inicio:", start_date, "|| Fecha fin:", end_date, "|| Duration:", (duration))

        
    
        # drop the beginning and ending of the measurement(15min)
        try:
            df = df.loc[start_date + pd.Timedelta(900, unit='seconds'):end_date - pd.Timedelta(900, unit='seconds')]
        except:
            pass

        #df['oca'] = df.apply(lambda x: db_limit(x['hour'],ld_limit= LIMITE_DIA , le_limit= LIMITE_TARDE ,ln_limit= LIMITE_NOCHE) , axis=1)
        #print(df)
        
        print("\n=================================")
        print("=================================\n")
        print("AFTER TRY AND EXCEPTS")
        print("\n=================================")
        print("=================================\n")
        
        
        if PLOT_TIME:
            make_timeplot(df, columns_dict=slm_dict, agg_period=PERIODO_AGREGACION, plotname=folder, percentiles=PERCENTILES)
        
        if PLOT_HEATMAP:
            plot_heatmap(df,values_column=slm_dict['LAEQ_COLUMN'], agg_func=leq,plotname=folder)
        
        if PLOT_DAY_EVOLUTION:
            plot_day_evolution(df,laeq_column=slm_dict["LAEQ_COLUMN"],plotname=folder)

        
        # add indicators column
        df['indicador_str'] = df.apply(lambda x: evaluation_period_str(x['hour']), axis=1)
        print(f'\n Indicador HOUR table (df["indicador_str"]):\n {df["indicador_str"]}')
                
        if PLOT_PERIOD_EVOLUTION:
            plot_period_evolution(df, laeq_column=slm_dict["LAEQ_COLUMN"], plotname=folder)

        if PLOT_INDHEATMAP:
            plot_indheatmap(df, plotname=folder, ind_column=slm_dict["LAEQ_COLUMN"])

        ############### INDICADORES NORMALES ###############
        ############################################################
        indicadores = get_day_levels(df, laeq_column=slm_dict['LAEQ_COLUMN'])
        
        print('\n##############################')
        print(f'Indicadores normales:\n {indicadores}')
        
        df_indicadores = pd.concat([df_indicadores, indicadores])
        print(f'\nDataFram Indicadores normales:\n {df_indicadores}')

        ################ INDICADORES VALENCIA ###############
        ############################################################
        # indicadores_valencia = get_day_levels_valencia(df, laeq_column=slm_dict['LAEQ_COLUMN'])
        # print('\n==========')
        # print(f'Indicadores valencia:\n {indicadores_valencia}')
        
        # df_indicadores_valencia = pd.concat([df_indicadores_valencia, indicadores_valencia])
        # print(f'\nDataFram Indicadores Valencia:\n {df_indicadores_valencia}')
        
        # df_indicadores_valencia.loc[df_indicadores_valencia['reg'].isnull(), 'reg'] = folder
        
        
        # add nights column

        df['night_str'] = df.apply(lambda x: add_night_column(x['hour'], x['weekday']), axis=1)
        print(f'\n Indicador HOUR table (df["night_str"]):\n {df["night_str"]}')

        if PLOT_NIGHT_EVOLUTION:
            plot_night_evolution(df,laeq_column=slm_dict["LAEQ_COLUMN"],plotname=folder)
        
        # WHY JUST TAKE 3???? ['R42', 'R42', 'R42', 'R43', 'R43', 'R43', 'R44', 'R44', 'R44', 'R45', 'R45', 'R45', 'R46', 'R46', 'R46', 'R47', 'R47', 'R47', 'R48', 'R48', 'R48', 'R49', 'R49', 'R49', 'R50', 'R50', 'R50', 'R51', 'R51', 'R51']
        n_registro.append([folder for i in range(3)])
        
        # n_registro_valencia.append([folder for i in range(2)])
        
        # formato comun
        map_dict = {slm_dict['LAEQ_COLUMN']  : "LAeq",
                    slm_dict['LAMAX_COLUMN'] : "LAmax",
                    slm_dict['LAMIN_COLUMN'] :'LAmin'}
        
        df_temp = df.copy()
        df_temp = df_temp.reset_index()
        print(f'\n******* df_temp:\n {df_temp}\n')
        
        df_temp = df_temp.rename(columns=map_dict)
        print(f'\n******* df_temp RENAME:\n {df_temp}\n')
         
         
        df_temp["ubicacion"] = folder # nombre de las carpetas obligatorio referencia a ubicación de la medida
        df_temp["slm_type"] = slm_type
        print(f'\n******* df_temp UBICACION SLM_TYPE:\n {df_temp}\n')
        
        
        df_temp = df_temp[common_columns]
        df_common_format = pd.concat([df_common_format,df_temp])
        print(f'\n******* df_temp COMMON + DF_TEMP:\n {df_temp}\n')
        
    except Exception as e:
        print(e)


flatten_list = [element for sublist in n_registro for element in sublist]
print(f'\nflatten_list {flatten_list}')

# flatten_list_VALENCIA = [element for sublist in n_registro_valencia for element in sublist]
# print(f"Flatten list valencia: {flatten_list_VALENCIA}")

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
