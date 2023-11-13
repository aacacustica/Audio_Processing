from datetime import datetime
import os
import pandas as pd

######################## SLM COLUMN MAPS #####################################
larsonlx_dict = {'LAEQ_COLUMN': 'LAeq',
'LAMAX_COLUMN': 'LAFmax',
'LAMIN_COLUMN': 'LAFmin'}

larson824_dict = {'LAEQ_COLUMN': 'Leq',
'LAMAX_COLUMN': 'Max',
'LAMIN_COLUMN': 'Min'}

larson814_dict = {'LAEQ_COLUMN': 'Leq',
'LAMAX_COLUMN': 'Max',
'LAMIN_COLUMN': 'Min'}

cesva_dict = {'LAEQ_COLUMN': 'LA1s',
'LAMAX_COLUMN': 'LAFmax1s',
'LAMIN_COLUMN': 'LAFmin1s'}

SV307_dict = {'LAEQ_COLUMN': 'LAeq (Ch1, P1) [dB]',
'LAMAX_COLUMN': 'LAFmax (Ch1, P1) [dB]',
'LAMIN_COLUMN': 'LAFmin (Ch1, P1) [dB]' 
} 

audiopost_dict = {'LAEQ_COLUMN': 'LA',
'LAMAX_COLUMN': 'LAmax',
'LAMIN_COLUMN': 'LAmin'}

common_columns = ["datetime", "LAeq", "LAmax", "LAmin","ubicacion","slm_type"]

day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

######################## Funciones Lectura #####################################
def get_data_814(filename: str):
    try:
        df = pd.read_csv(filename, header=16, encoding='latin1')
    except UnicodeDecodeError:
        df = pd.read_csv(filename, header=16)
    if "Leq" not in df.columns:
        df = pd.read_csv(filename, header=19, sep=';', encoding='latin1')
    df['datetime'] = pd.to_datetime(df['Date'] + ' ' + df['Time'])
    return df

def get_data_lx_ES(filename: str):
    df = pd.read_excel(filename, sheet_name='Historia del tiempo')
    df['datetime'] = pd.to_datetime(df['Fecha'])
    return df

def get_data_824(filename: str):
    df = pd.read_csv(filename, sep=',', encoding='latin1', header=15)
    df = df.dropna(axis=1)
    if "Leq" not in df.columns:
        df = pd.read_csv(filename,header=15, sep=',')
    df['datetime'] = pd.to_datetime(df['Date'] + ' '+ df['Time'])
    return df

def get_data_SV307(filename: str):
    df = pd.read_csv(filename,header=14,skipfooter=8,usecols=[0,1,2,3,4,5,6,7,8], engine='python')
    if 'LAeq (Ch1, P1) [dB]' not in df.columns:
        df = pd.read_csv(filename,header=14,sep=';',skipfooter=8,usecols=[0,1,2,3,4,5,6,7,8], engine='python')
    df['datetime'] = pd.to_datetime(df['Time'],format="%d/%m/%Y %H:%M:%S")
    return df
    
def get_data_lx_EN(filename: str):
    df = pd.read_excel(filename,sheet_name=4)
    df['datetime'] = pd.to_datetime(df['Date'])
    return df

def get_data_audio(filename: str):
    df = pd.read_csv(filename)
    df['datetime'] = pd.to_datetime(df['date'])
    return df 

def get_data_cesva(measurement_folder: str):
    if os.path.isfile(measurement_folder):
        cesva_index = measurement_folder.find('CESVA')
        if cesva_index != -1:
            measurement_folder = measurement_folder[:cesva_index] + 'CESVA'
        else:
            raise ValueError("CESVA folder not found in the file path.")

    elif 'CESVA' not in measurement_folder:
        raise ValueError("The directory does not contain 'CESVA'.")
    
    cesva_files = []
    cols_to_use = ['Date hour','Elapsed t','LA1s','LAFmax1s','LAFmin1s']
    for root, dirs, files in os.walk(measurement_folder, topdown=False):
        for name in files:
            if name.endswith('.csv'):
                cesva_files.append(os.path.join(root, name))

    df_all = pd.DataFrame()
    for file_path in cesva_files:
        try:
            df = pd.read_csv(file_path,sep=';',header=11,decimal=',', usecols=cols_to_use)
            df.dropna(subset=['Elapsed t'],inplace=True) 
        except Exception as e: 
            pass
        try:
            df = pd.read_csv(file_path,sep=';',header=12,decimal=',',usecols=cols_to_use)
            df.dropna(subset=['Elapsed t'],inplace=True)   
        except Exception as e: 
            pass
        
        #df = df[['Date hour','Elapsed t','LA1s','LAFmax1s','LAFmin1s']]
        df_all = pd.concat([df_all,df])
        
    df = df_all.copy()
    del df_all
    for col in df.columns:
        if col not in  ["Date hour", "Elapsed t"]:
            df[col] = pd.to_numeric(df[col])
    
    df['datetime'] = df.apply(lambda x: datetime.strptime(x['Date hour'], '%d/%m/%Y %H:%M:%S'),axis=1)
    df['datetime'] = pd.to_datetime(df['datetime'])
    return df