from datetime import datetime
import os
import pandas as pd

def get_data_814(filename: str):
    """Getting data from Larson Davis 814 SLM
    Args:
        filename: path to the measurement file
    Returns:
        df: pandas DataFrame with the measurement data
    """
    try:
        df = pd.read_csv(filename, header=16, encoding='latin1')
   
    except UnicodeDecodeError:
        df = pd.read_csv(filename, header=16)
   
    if "Leq" not in df.columns:
        df = pd.read_csv(filename, header=19, sep=';', encoding='latin1')
   
    df['datetime'] = pd.to_datetime(df['Date'] + ' ' + df['Time'])
    return df

def get_data_lx_ES(filename: str):
    """Getting data from Lx Es
    Args:
        filename: path to the measurement file
    Returns:
        df: pandas DataFrame with the measurement data
    """
    df = pd.read_excel(filename, sheet_name='Historia del tiempo')
    df['datetime'] = pd.to_datetime(df['Fecha'])
    
    return df

def get_data_824(filename: str):
    """Getting data from Larson Davis 824 SLM
    Args:
        filename: path to the measurement file
    Returns:
        df: pandas DataFrame with the measurement data"""
    df = pd.read_csv(filename, sep=',', encoding='latin1', header=15)
    df = df.dropna(axis=1)
    
    if "Leq" not in df.columns:
        df = pd.read_csv(filename,header=15, sep=',')
    
    df['datetime'] = pd.to_datetime(df['Date'] + ' '+ df['Time'])
    return df

def get_data_SV307(filename: str):
    """Getting data from Svantek SV307 SLM
    Args:
        filename: path to the measurement file
    Returns:
        df: pandas DataFrame with the measurement data"""
    df = pd.read_csv(filename,header=14,skipfooter=8,usecols=[0,1,2,3,4,5,6,7,8], engine='python')
    
    if 'LAeq (Ch1, P1) [dB]' not in df.columns:
        df = pd.read_csv(filename,header=14,sep=';',skipfooter=8,usecols=[0,1,2,3,4,5,6,7,8], engine='python')
    
    df['datetime'] = pd.to_datetime(df['Time'],format="%d/%m/%Y %H:%M:%S")
    return df
    
def get_data_lx_EN(filename: str):
    """Getting data from Lx En
    Args:
        filename: path to the measurement file
    Returns:
        df: pandas DataFrame with the measurement data
    """
    df = pd.read_excel(filename,sheet_name=4)
    df['datetime'] = pd.to_datetime(df['Date'])
    return df

def get_data_audio(filename: str):
    """Getting data from AudioPost SLM

    Args:
        filename (str): path to the measurement file

    Returns:
        df: pandas DataFrame with the measurement data
    """
    df = pd.read_csv(filename)
    df['datetime'] = pd.to_datetime(df['date'])
    return df 

def get_data_cesva(measurement_folder: str):
    """Getting data from CESVA SLM
    Args:
        measurement_folder: path to the measurement folder
    Returns:
        df: pandas DataFrame with the measurement data
    """
    # Check if the measurement folder is a file
    if os.path.isfile(measurement_folder):
        cesva_index = measurement_folder.find('CESVA')
        # If the file is in a CESVA folder, get the folder path
        if cesva_index != -1:
            measurement_folder = measurement_folder[:cesva_index] + 'CESVA'
        else:
            raise ValueError("CESVA folder not found in the file path.")
    # Check if the measurement folder is a directory
    elif 'CESVA' not in measurement_folder:
        raise ValueError("The directory does not contain 'CESVA'.")
    
    cesva_files = []
    cols_to_use = ['Date hour','Elapsed t','LA1s','LAFmax1s','LAFmin1s']
    
    # Get all the files in the measurement folder
    for root, dirs, files in os.walk(measurement_folder, topdown=False):
        for name in files:
            if name.endswith('.csv'):
                cesva_files.append(os.path.join(root, name))
    
    df_all = pd.DataFrame()
    # Read all the files in the measurement folder
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
        
        # Add the measurement location to the dataframe
        #df = df[['Date hour','Elapsed t','LA1s','LAFmax1s','LAFmin1s']]
        # Add the measurement location to the dataframe
        df_all = pd.concat([df_all,df])
    
    # Copy dataframe
    df = df_all.copy()
    # Delete the original dataframe
    del df_all
    # convert to numeric values
    for col in df.columns:
        if col not in  ["Date hour", "Elapsed t"]:
            df[col] = pd.to_numeric(df[col])
    
    # Add the datetime column to the dataframe
    df['datetime'] = df.apply(lambda x: datetime.strptime(x['Date hour'], '%d/%m/%Y %H:%M:%S'),axis=1)
    df['datetime'] = pd.to_datetime(df['datetime'])
    
    return df