import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

# octave bands list
octave_bands = [
    '12.4', '15.62', '19.69', '24.8', '31.25', '39.37', '49.61', '62.5', '78.75', '99.21',
    '125.0', '157.49', '198.43', '250.0', '314.98', '396.85', '500.0', '629.96', '793.7', 
    '1000.0', '1259.92', '1587.4', '2000.0', '2519.84', '3174.8', '4000.0', '5039.68',
    '6349.6', '8000.0', '10079.37', '12699.21', '16000.0', '20158.74'
]

# desired time interval to analyze
time_intervals = [
    ("2022-04-05 10:00:00", "2022-04-05 11:00:00"),
    ("2022-04-05 18:00:00", "2022-04-05 19:00:00"),
    ("2022-04-06 04:00:00", "2022-04-06 05:00:00"),
    ("2022-04-07 08:00:00", "2022-04-07 09:00:00")
]

def octave_band(file, start_time, end_time):
    df = pd.read_csv(file, sep=',')
    df.set_index('date', inplace=True)
    df_filtered = df.loc[start_time:end_time]
    df_filtered = df_filtered[octave_bands]
    df_filtered = df_filtered[df_filtered != -float('inf')]
    df_filtered = df_filtered.drop(columns=['20158.74'])
    return df_filtered

def plot_spectrogram_octave(df_filtered, start_time, end_time):
    times = df_filtered.index
    frequencies = df_filtered.columns.astype(float)
    values = df_filtered.values.T
    
    start_dt = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
    end_dt = datetime.strptime(end_time, "%Y-%m-%d %H:%M:%S")
    ticks_intervals = [start_dt + timedelta(minutes=i) for i in range(0, int((end_dt - start_dt).total_seconds() / 60) + 1, 10)]
    
    ticks_intervals_str = [time.strftime("%Y-%m-%d %H:%M:%S") for time in ticks_intervals]
    tick_labels = [time.strftime("%H:%M:%S") for time in ticks_intervals]

    plt.figure(figsize=(23, 10))
    plt.pcolormesh(times, frequencies, values, shading='auto', cmap='inferno')
    plt.colorbar(label='Magnitude (dB)')
    plt.yscale('log')
    plt.ylabel('Frequency (Hz)')
    plt.xlabel('Time')
    plt.title(f'Spectrogram from {start_time} to {end_time}')
    plt.xticks(ticks_intervals_str, tick_labels)
    plt.tight_layout()
    plt.show()

def main():
    file_path = "C:/Users/GIS2/Documents/tratamiento_audios/tratamiento_audio/tenerife-20220404/tenerife-20220404_sploct.csv"
    for start_time, end_time in time_intervals:
        df = octave_band(file_path, start_time, end_time)
        plot_spectrogram_octave(df, start_time, end_time)

if '__main__' == "__main__":
    main()
