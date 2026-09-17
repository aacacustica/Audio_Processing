from datetime import datetime
import os
import pandas as pd
from utils import change_date_and_time



def get_data_bilbo(file_path: str, logger, new_date=None, new_time=None, new_threshold_date=None, new_threshold_time=None):
    try:
        df = pd.read_csv(file_path)
    except:
        df = pd.read_csv(file_path, encoding='latin1', sep=';')

    try:
        df['datetime'] = pd.to_datetime(df['datetime'], errors='raise')
    except KeyError:
        logger.info("No 'datetime' column found in CSV.")
    except pd.errors.OutOfBoundsDatetime:
        logger.error("Error converting 'datetime' column.")
    
    try:    
        df = change_date_and_time(df, new_date, new_time, new_threshold_date, new_threshold_time, logger)
    
    except Exception as e:
        logger.error(f"Error: {e}")
        return None
    return df



def get_data_814(file_path: str, logger, new_date=None, new_time=None, new_threshold_date=None, new_threshold_time=None):
    try:
        df = pd.read_csv(file_path, header=16, encoding='latin1')
    except UnicodeDecodeError:
        df = pd.read_csv(file_path, header=16)
   
    if "Leq" not in df.columns:
        df = pd.read_csv(file_path, header=19, sep=';', encoding='latin1')
    df['datetime'] = pd.to_datetime(df['Date'] + ' ' + df['Time'])

    try:    
        df = change_date_and_time(df, new_date, new_time, new_threshold_date, new_threshold_time, logger)
    
    except Exception as e:
        logger.info(f"Error: {e}")
        return None
    return df




def get_data_lx_ES(file_path: str, logger, new_date=None, new_time=None, new_threshold_date=None, new_threshold_time=None):
    df = pd.read_excel(file_path, sheet_name='Historia del tiempo')
    df['datetime'] = pd.to_datetime(df['Fecha'])

    try:    
        df = change_date_and_time(df, new_date, new_time, new_threshold_date, new_threshold_time, logger)
    
    except Exception as e:
        logger.error(f"Error: {e}")
        return None

    return df




def get_data_lx_EN(file_path: str,logger, new_date=None, new_time=None, new_threshold_date=None, new_threshold_time=None):
    df = pd.read_excel(file_path,sheet_name=4)
    df['datetime'] = pd.to_datetime(df['Date'])

    try:    
        df = change_date_and_time(df, new_date, new_time, new_threshold_date, new_threshold_time, logger)
    
    except Exception as e:
        logger.error(f"Error: {e}")
        return None
    return df



def get_data_824(file_path: str,logger, new_date=None, new_time=None, new_threshold_date=None, new_threshold_time=None):
    df = pd.read_csv(file_path, sep=',', encoding='latin1', header=15)
    df = df.dropna(axis=1)
    
    if "Leq" not in df.columns:
        df = pd.read_csv(file_path,header=15, sep=',')
    
    df['datetime'] = pd.to_datetime(df['Date'] + ' '+ df['Time'])

    try:    
        df = change_date_and_time(df, new_date, new_time, new_threshold_date, new_threshold_time, logger)
    
    except Exception as e:
        logger.error(f"Error: {e}")
        return None
    
    return df




def read_SV307(file_path: str, logger):
    df = None  
    read_attempts = [
        {"header": 3, "sep": ";", "label": "header 19"},
        {"header": 14, "sep": ";", "label": "header 14"},
        {"header": 13, "sep": None, "label": "header 13 without ';'"},
        {"header": 18, "sep": None, "label": "header 18"},
        {"header": 6,  "sep": ";", "label": "header 6"}
    ]
    for attempt in read_attempts:
        try:
            logger.info(f"Reading SV307 file with {attempt['label']}")
            df_temp = pd.read_csv(
                file_path,
                header=attempt["header"],
                sep=attempt["sep"],
                skipfooter=8,
                engine='python'
            )

            df_temp.columns = [str(col).strip() for col in df_temp.columns]

            logger.info(f"Correctly read SV307 file with {attempt['label']}")
            logger.info(f"Columns found: {df_temp.columns.tolist()}")

            column_lookup = {str(col).strip().lower(): col for col in df_temp.columns}

            if "time" in column_lookup or "Time" in column_lookup: datetime_col = column_lookup['date & time']
            elif "date & time" in column_lookup: datetime_col = column_lookup['date & time']
            else: 
                logger.warning(f"Neither 'Time' nor 'Date & Time' found using {attempt['label']}")
                continue

            df = df_temp
            logger.info(f"Valid SV307 format found with {attempt['label']} | datetime column:  {datetime_col}")
            break

        except Exception as e:
            logger.warning(f"Failed attempt with {attempt['label']}: {e}")
            continue


    if df is None: 
        logger.error(f"Could not find a valid SV307 format for: {file_path}")
        return None

    logger.info(f"Length of the file: {len(df)}")

    # ============================================================
    # NORMALIZE THIS SV307 FORMAT
    # ============================================================

    rename_map = {}

    if 'Unnamed: 2' in df.columns: rename_map["Unnamed: 2"] = "LAFmax (TH) [dB]"
    if "Unnamed: 3" in df.columns: rename_map['Unnamed: 3'] = "LAFmin (TH) [dB]"
    if "Unnamed: 4" in df.columns: rename_map['Unnamed: 4'] = "LAeq (TH) [dB]"

    if rename_map:
        df = df.rename(columns=rename_map)
        
        logger.info(f"Renamed SV307 columns: {rename_map}")

    df.rename(
        columns = {
            # Formato SV307 antiguo
            'LAeq (Ch1, P1) [dB]': 'LAeq',
            'LAFmax (Ch1, P1) [dB]': 'LAFmax',
            'LAFmin (Ch1, P1) [dB]': 'LAFmin',

            # Formato SV307 nuevo / TH
            'LAeq (TH) [dB]': 'LAeq',
            'LAFmax (TH) [dB]': 'LAFmax',
            'LAFmin (TH) [dB]': 'LAFmin',
        }, inplace  = True
    )
    logger.info(  f"SV307 final acoustic columns: " f"{[c for c in ['LAeq', 'LAFmax', 'LAFmin'] if c in df.columns]}")
    # ================================= ===========================
    # DATETIME
    # ============================================================

    try:
        logger.info(f"Trying to change '{datetime_col}' column to 'datetime' column")

        parsed_datetime = pd.to_datetime(df[datetime_col],format="%d/%m/%Y %H:%M:%S",errors='coerce')
        invalid_dates = int(parsed_datetime.isna().sum())

        if invalid_dates > 0: logger.warning(f"Dropping {invalid_dates} rows with invalid datetime")

        valid_mask = parsed_datetime.notna()

        df = df.loc[valid_mask].copy()

        df['datetime'] = (parsed_datetime.loc[valid_mask])

        logger.info(f"Converted '{datetime_col}' column to datetime.")
        logger.info(f"SV307 datetime range: {df['datetime'].min()} -> {df['datetime'].max()}")

    except Exception as e:
        logger.error(f"Error converting SV307 datetime: {e}")
        return None

    return df


def get_data_SV307(file_path: str,logger, new_date=None, new_time=None, new_threshold_date=None, new_threshold_time=None):
    logger.info("Testing how many SV307 files are in the folder")
    # testing if there are more than 1 csv file in the folder
    folder_path = file_path.split('/')[:-1]
    # joining the elements
    folder_path = '/'.join(folder_path)

    # counting how many csv files are in the folder:
    csv_files = [f for f in os.listdir(folder_path) if f.endswith('.csv')]
    logger.info(f"Number of csv files in the folder: {len(csv_files)}")
    
    if len(csv_files) > 1:
        logger.info("Concatenating all the csv files in the folder and ordering them by date")
        df_all = []
        for file in csv_files:
            file_path = os.path.join(folder_path, file)
            try:
                df = read_SV307(file_path, logger)
                logger.info(f"Reading file: {file_path}")
            except Exception as e:
                filename = file_path.split('\\')[-1]
                logger.error(f"Error reading file: {filename}")
                logger.error(f"Error: {e}")
                continue

            df_all.append(df)

        df = pd.concat(df_all)
        # order it by datetime
        df = df.sort_values(by='datetime')
        # remove column name Unnamed:
        df = df.loc[:, ~df.columns.str.contains('^Unnamed')]

    else:
        # read the only csv file in the folder
        try:
            logger.info("Trying to read with the read_SV307 function the single file")
            df = read_SV307(file_path, logger)
        except Exception as e:
            logger.error(f"Error reading file: {file_path}")
            logger.error(f"Error: {e}")
            return None
        
    try:    
        df = change_date_and_time(df, new_date, new_time, new_threshold_date, new_threshold_time, logger)
        logger.info("Changing date and time")
    
    except Exception as e:
        logger.error(f"Error: {e}")
        return None
    
    
    df.rename(columns={'LAeq (Ch1, P1) [dB]': 'LAeq',
                       'LAFmax (Ch1, P1) [dB]': 'LAFmax',
                       'LAFmin (Ch1, P1) [dB]': 'LAFmin'}, inplace=True)
    
    # df = df[['datetime','LAeq','LAFmax','LAFmin']]
    logger.info(f"Final length of the file: {len(df)}")
    return df



def get_data_audiomoth(file_path: str,logger, new_date=None, new_time=None, new_threshold_date=None, new_threshold_time=None):
    df = pd.read_csv(file_path)
    if 'Time' in df.columns:
        df['datetime'] = pd.to_datetime(df['Time'], format='%Y-%m-%d_%H:%M:%S')
    else:
        df['datetime'] = pd.to_datetime(df['date'])
    

    try:    
        df = change_date_and_time(df, new_date, new_time, new_threshold_date, new_threshold_time, logger)
    
    except Exception as e:
        logger.error(f"Error: {e}")
        return None
    
    return df 



def get_data_cesva(measurement_folder: str, logger, new_date=None, new_time=None, new_threshold_date=None, new_threshold_time=None):
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

    try:    
        df = change_date_and_time(df, new_date, new_time, new_threshold_date, new_threshold_time, logger)
    
    except Exception as e:
        logger.error(f"Error: {e}")
        return None
    
    return df



def get_data_bruel_kjaer(measurement_folder: str, logger, new_date=None, new_time=None, new_threshold_date=None, new_threshold_time=None):
    if os.path.isfile(measurement_folder):
        # remove last part of the path to get the folder
        measurement_folder = measurement_folder.split('\\')[:-1]
        #join
        measurement_folder = '\\'.join(measurement_folder)

        #check if the folder exists
        if not os.path.exists(measurement_folder):
            logger.error(f"Folder {measurement_folder} does not exist")
            return None

        
        files = os.listdir(measurement_folder)
        dfs = []
        sheet_name = 'LoggedBB'

        for fname in files:
            if not fname.endswith('.xlsx'):
                continue

            file_path = os.path.join(measurement_folder, fname)
            try:
                logger.info(f"Reading files...")
                df = pd.read_excel(file_path, sheet_name=sheet_name)
                df['datetime'] = pd.to_datetime(df["Start Time"], format='%d/%m/%Y %H:%M:%S')
                dfs.append(df)

            except Exception as e:
                logger.error(f"Error reading file: {file_path} --> {e}")
                continue

        if dfs:
            df_all = pd.concat(dfs, ignore_index=True)
        else:
            df_all = pd.DataFrame()
        
        # sort the dataframe by datetime
        df_all = df_all.sort_values(by='datetime')

        return df_all
        