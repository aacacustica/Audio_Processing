import os
import pandas as pd

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
    folder_path = r"\\192.168.205.117\AAC_Server\OCIO\24052_ZARAUTZ\CAMPAÑA_2\3-Medidas\ZARAUTZ_C2_P6\SONOMETRO"
    df = concatenate_csv_files(folder_path)
    print(df)

    # order by datetime
    df = df.sort_values(by='datetime')
    # exit()

    # save csv in the folder_path
    df.to_csv(os.path.join(folder_path, "concatenated.csv"), index=False)
    print("CSV file saved")


if __name__ == '__main__':
    main()