import os
import pandas as pd


def get_data_lx_ES(filename: str):
    df = pd.read_excel(filename, sheet_name='Historia del tiempo')
    df['Fecha'] = pd.to_datetime(df['Fecha'])
    # add a day beacuse there is a bug in the data
    # df['datetime'] = df['datetime'] + pd.DateOffset(days=1)
    return df


def change_df_time(df, date_col, date_correction):
    """change the fist date of the dataframe to date_correction and then
    add the difference to the rest of the dates"""
    first_date = df[date_col].iloc[0]
    difference = date_correction - first_date
    df[date_col] = df[date_col] + difference
    
    return df


def main():
    csv_file = r"\\192.168.205.117\AAC_Server\OCIO\24052_ZARAUTZ\CAMPAÑA_1\3-Medidas\ZARAUTZ_C1_P2\SONOMETRO\LxT_0002523-20240715 143625-LxT_Data.007.xlsx"
    if os.path.exists(csv_file):
        print("READING DATA...")
        df = get_data_lx_ES(csv_file)
        print(df.head())
    else:
        print(f"File {csv_file} does not exist")

    print("CORRECTING TIME...")
    year_month_day = '2024-07-17'
    hour_minute_second = '12:08:08' 

    date_correction = pd.to_datetime(year_month_day + ' ' + hour_minute_second)

    df_corrected = change_df_time(df, 'Fecha', date_correction)
    print(df_corrected.head())

    # save the corrected dataframe
    print("SAVING CORRECTED DATA...")
    df_corrected.to_csv(os.path.join(os.path.dirname(csv_file), "corrected.csv"), index=False)
    


if __name__ == "__main__":
    main()