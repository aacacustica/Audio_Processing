import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import argparse
import os
plt.style.use("bmh")

octave_bands = [
    '12.4', '15.62', '19.69', '24.8', '31.25', '39.37', '49.61', '62.5', '78.75', '99.21',
    '125.0', '157.49', '198.43', '250.0', '314.98', '396.85', '500.0', '629.96', '793.7', 
    '1000.0', '1259.92', '1587.4', '2000.0', '2519.84', '3174.8', '4000.0', '5039.68',
    '6349.6', '8000.0', '10079.37', '12699.21', '16000.0', '20158.74'
]

def get_name(file: str):
    return os.path.basename(file).split('.')[0].split('_')[0]

def get_path(file: str):
    return os.path.dirname(file)

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

def plot_spectrogram_octave(path: str, df_filtered, file_name: str, interval_minutes: int, start_time=None, end_time=None):
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
    plt.gca().xaxis.set_major_locator(mdates.MinuteLocator(interval=interval_minutes))
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M'))

    # Rotate date labels for clarity
    plt.xticks(rotation=90)

    plt.title(f'Spectrogram {file_name}')
    plt.tight_layout()
    
    os.makedirs(f'{path}/Spectrogram', exist_ok=True)
    if start_time and end_time:
        plt.savefig(f'{path}/Spectrogram/{file_name}_spect_oct_detail.png')
    else:
        plt.savefig(f'{path}/Spectrogram/{file_name}_spect_oct.png')

def argument_parser():
    parser = argparse.ArgumentParser(description='Plot Spectrogram from CSV File')
    parser.add_argument('-p', '--path', required=True, type=str, help='Path to the CSV file')
    parser.add_argument('-i', '--interval', required=False, type=int, default=300, help='Interval in minutes for x-axis ticks')
    parser.add_argument('-s', '--start', required=False, type=str, help='Start time for the spectrogram')
    parser.add_argument('-e', '--end', required=False, type=str, help='End time for the spectrogram')
    args = parser.parse_args()
    return args

def main():
    args = argument_parser()
    csv_file = args.path
    interval_minutes = args.interval
    start_time = args.start
    end_time = args.end

    file_name = get_name(csv_file)
    path = get_path(csv_file)
    
    df = octave_band(csv_file, start_time, end_time)
    plot_spectrogram_octave(path, df, file_name, interval_minutes, start_time, end_time)

if __name__ == "__main__":
    main()