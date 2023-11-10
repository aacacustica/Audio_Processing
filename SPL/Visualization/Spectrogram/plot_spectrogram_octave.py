import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import argparse
import os

# octave bands list
octave_bands = [
    '12.4', '15.62', '19.69', '24.8', '31.25', '39.37', '49.61', '62.5', '78.75', '99.21',
    '125.0', '157.49', '198.43', '250.0', '314.98', '396.85', '500.0', '629.96', '793.7', 
    '1000.0', '1259.92', '1587.4', '2000.0', '2519.84', '3174.8', '4000.0', '5039.68',
    '6349.6', '8000.0', '10079.37', '12699.21', '16000.0', '20158.74'
]

def get_name(file: str):
    return os.path.basename(file).split('.')[0]

def octave_band(file: str, start_time=None, end_time=None):
    df = pd.read_csv(file, sep=',')
    df['date'] = pd.to_datetime(df['date'])
    df.set_index('date', inplace=True)

    if start_time and end_time:
        df_filtered = df.loc[start_time:end_time]
    else:
        df_filtered = df

    df_filtered = df_filtered[octave_bands]
    df_filtered = df_filtered[df_filtered != -float('inf')]
    df_filtered = df_filtered.drop(columns=['20158.74'])
    return df_filtered

def plot_spectrogram_octave(df_filtered, file_name: str, interval_hours: int):
    frequencies = df_filtered.columns.astype(float)
    values = df_filtered.values.T
    valid_frequencies = frequencies[~np.all(np.isnan(values) | np.isinf(values), axis=1)]

    # Creating a list of frequency labels from the valid octave bands
    freq_labels = [f"{freq} Hz" for freq in valid_frequencies]

    plt.figure(figsize=(23, 10))
    plt.pcolormesh(df_filtered.index, range(len(valid_frequencies)), values[frequencies.searchsorted(valid_frequencies)], shading='auto', cmap='inferno')
    plt.colorbar(label='Magnitude (dB)')

    # Set y-axis to use valid octave band frequencies as labels
    plt.yticks(range(len(valid_frequencies)), freq_labels)
    plt.ylabel('Frequency (Hz)')
    plt.xlabel('Time')

    # Set x-axis to specified hour intervals
    plt.gca().xaxis.set_major_locator(mdates.HourLocator(interval=interval_hours))
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M'))

    # Rotate date labels for clarity
    plt.xticks(rotation=90)

    plt.title(f'Spectrogram {file_name}')
    plt.tight_layout()
    plt.show()


def argument_parser():
    parser = argparse.ArgumentParser(description='Plot Spectrogram from CSV File')
    parser.add_argument('-p', '--path', required=True, type=str, help='Path to the CSV file')
    parser.add_argument('-i', '--interval', required=False, type=int, default=5, help='Interval in hours for x-axis ticks')
    args = parser.parse_args()
    return args

def main():
    args = argument_parser()
    file_path = args.path
    interval_hours = args.interval
    file_name = get_name(file_path)
    
    df = octave_band(file_path)
    plot_spectrogram_octave(df, file_name, interval_hours)

if __name__ == "__main__":
    main()