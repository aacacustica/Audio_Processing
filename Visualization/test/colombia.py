import os
import pandas as pd
import numpy as np
import argparse


def leq(levels):
    levels = levels[~np.isnan(levels)]
    l = np.array(levels)
    return 10*np.log10(np.mean(np.power(10,l/10)))


def power_avg_colum(df_path, column_name='LA'):
    df = pd.read_csv(df_path)
    # make power average with the formuyla, and the LA colum
    # power_aveg = leq(df['LA'])
    power_aveg = leq(df[column_name])
    #round 2 decimals
    power_aveg = round(power_aveg, 2)

    # name
    name = df_path.split('\\')[-3]
    print(f"{name} --> {power_aveg} dBs")
    print()


def parse_arguments():
    parser = argparse.ArgumentParser(description='Calculate SPL levels for audio files in a directory')
    parser.add_argument('-p', '--path', type=str, required=False, help='Directory to be processed')
    return parser.parse_args()



def main():
    args = parse_arguments()
    # df_path = args.path

    df_path_aranjuez = r"\\192.168.205.123\aac_server\HANDIA\COLOMBIA\CALIBRACION\3-Medidas\aranjuez\AUDIOMOTH\leq_aranjuez_v3_0.csv"
    df_path_bello = r"\\192.168.205.123\aac_server\HANDIA\COLOMBIA\CALIBRACION\3-Medidas\Punto_Bello\AUDIOMOTH\leq_Punto_Bello_v3_0.csv"

    power_avg_colum(df_path_aranjuez)
    power_avg_colum(df_path_bello)


if __name__ == '__main__':
    main()