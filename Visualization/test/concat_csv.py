import os
import pandas as pd


def get_title(filename: str):
    title = filename.split('\\')[-2]
    return title


def get_data_SV307(filename: str):
    try:
        df = pd.read_csv(filename,header=14,sep=';',skipfooter=8,usecols=[0,1,2,3,4,5,6,7,8], engine='python')
    except Exception as e:
        df = pd.read_csv(filename,header=18,skipfooter=8,usecols=[0,1,2,3,4,5,6,7,8], engine='python')
    
    if not 'LAeq (Ch1, P1) [dB]' in df.columns:
        df = pd.read_csv(filename,header=18,skipfooter=8,usecols=[0,1,2,3,4,5,6,7,8], engine='python', sep=';')

    df = df[pd.to_datetime(df['Time'], format='%d/%m/%Y %H:%M:%S', errors='coerce').notnull()]
    df['datetime'] = pd.to_datetime(df['Time'], format='%d/%m/%Y %H:%M:%S')
    
    df.rename(columns={'LAeq (Ch1, P1) [dB]': 'LAeq',
                       'LAFmax (Ch1, P1) [dB]': 'LAFmax',
                       'LAFmin (Ch1, P1) [dB]': 'LAFmin'}, inplace=True)

    return df


def get_data_lx_ES(file_path: str):
    df = pd.read_excel(file_path, sheet_name='Historia del tiempo')
    df['datetime'] = pd.to_datetime(df['Fecha'])
   
    return df
 

def concatenate_csv_files(folder_path: str):
    # get all the files in the folder
    files = os.listdir(folder_path)
    # filter only csv files
    csv_files = [file for file in files if file.endswith(".csv")]
    # print(csv_files)

    # read all the csv files
    dfs = []
    for file in csv_files:
        file_path = os.path.join(folder_path, file)
        print(file_path)
        df = get_data_SV307(file_path)
        # print(df)
        # print(df.columns)
        # exit()
        # order by datetime
        # df = df.sort_values(by='Time')
        # print(df)
        dfs.append(df)
    
    # concatenate all the dataframes
    df = pd.concat(dfs)
    return df



def main():
    folder_path = r"\\192.168.205.123\aac_server\INDUSTRIA\24027_ERRENTERIA_MR\CAMPAÑA_1\3-Medidas\ERRENTERIA_C1P1\SONOMETRO"
    title = get_title(folder_path)
    print(title)


    df = concatenate_csv_files(folder_path)

    # order by datetime
    df = df.sort_values(by='datetime')
    print(df)
    # exit()

    # save csv in the folder_path
    exit()
    df.to_csv(os.path.join(folder_path, f"Svantek_{title}.csv"), index=False)
    print("CSV file saved")


if __name__ == '__main__':
    main()