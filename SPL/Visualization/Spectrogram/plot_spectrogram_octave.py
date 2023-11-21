import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import argparse
import os
import librosa
import librosa.display
plt.style.use("bmh")

octave_bands = [
    '12.4', '15.62', '19.69', '24.8', '31.25', '39.37', '49.61', '62.5', '78.75', '99.21',
    '125.0', '157.49', '198.43', '250.0', '314.98', '396.85', '500.0', '629.96', '793.7', 
    '1000.0', '1259.92', '1587.4', '2000.0', '2519.84', '3174.8', '4000.0', '5039.68',
    '6349.6', '8000.0', '10079.37', '12699.21', '16000.0', '20158.74'
]

bands_multifunction = [31.5, 63, 125, 250, 500, 1000, 2000, 4000, 8000, 12500, 16000]

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

    freq_labels = [f"{freq} Hz" for freq in valid_frequencies]

    plt.figure(figsize=(23, 10))
    plt.pcolormesh(df_filtered.index, range(len(valid_frequencies)), values[frequencies.searchsorted(valid_frequencies)], shading='auto', cmap='inferno')
    plt.colorbar(label='Magnitude (dB)')

    plt.yticks(range(len(valid_frequencies)), freq_labels)
    plt.ylabel('Frequency (Hz)')
    plt.xlabel('Time')

    plt.gca().xaxis.set_major_locator(mdates.MinuteLocator(interval=interval_minutes))
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M'))

    plt.xticks(rotation=90)

    plt.title(f'Spectrogram {file_name}')
    plt.tight_layout()
    
    os.makedirs(f'{path}/Spectrogram', exist_ok=True)
    if start_time and end_time:
        plt.savefig(f'{path}/Spectrogram/{file_name}_spect_oct_detail.png')
    else:
        plt.savefig(f'{path}/Spectrogram/{file_name}_spect_oct.png')

def plot_spectrogram_audio(file_path, path, file_name, n_fft=2048, hop_length=512, win_length=None):
    y, sr = librosa.load(file_path, sr=None)

    # Calculate the Short-Time Fourier Transform (STFT)
    D = np.abs(librosa.stft(y, n_fft=n_fft, hop_length=hop_length, win_length=win_length))
    # Convert amplitude to decibels
    DB = librosa.amplitude_to_db(D, ref=np.max)
    # Get the frequencies for each bin in the STFT
    freqs = librosa.core.fft_frequencies(sr=sr, n_fft=n_fft)

    # Filter out only the rows corresponding to the desired frequencies
    min_freq = min(bands_multifunction)
    max_freq = max(bands_multifunction)
    freq_indices = np.where((freqs >= min_freq) & (freqs <= max_freq))[0]
    DB_filtered = DB[freq_indices, :]

    # Plot the spectrogram
    plt.figure(figsize=(15, 6))
    librosa.display.specshow(DB_filtered, sr=sr, hop_length=hop_length, x_axis='time', y_axis='log', fmin=min_freq, fmax=max_freq)
    plt.colorbar(format='%+2.0f dB')
    plt.title(f'Spectrogram {file_name}')
    
    # Save the plot
    os.makedirs(f'{path}/Spectrogram', exist_ok=True)
    plt.savefig(f'{path}/Spectrogram/{file_name}_spectrogram.png')
    plt.close()



def argument_parser():
    parser = argparse.ArgumentParser(description='Plot Spectrogram from CSV File')
    parser.add_argument('-p', '--path', required=True, type=str, help='Path to the CSV file')
    parser.add_argument('-i', '--interval', required=False, type=int, default=300, help='Interval in minutes for x-axis ticks')
    parser.add_argument('-s', '--start', required=False, type=str, help='Start time for the spectrogram')
    parser.add_argument('-e', '--end', required=False, type=str, help='End time for the spectrogram')
    parser.add_argument('-t', '--type', required=False, type=str, default="csv", choices=['csv', 'audio'], help='File type: csv or audio')
    args = parser.parse_args()
    return args

def process_audio_file(file_path):
    file_name = get_name(file_path)
    path = get_path(file_path)
    plot_spectrogram_audio(file_path, path, file_name)

def main():
    args = argument_parser()
    file_path = args.path
    file_type = args.type

    if file_type == 'audio':
        if os.path.isdir(file_path):
            for audio_file in os.listdir(file_path):
                full_audio_path = os.path.join(file_path, audio_file)
                if os.path.isfile(full_audio_path) and audio_file.lower().endswith(('.wav', '.mp3', '.flac', '.WAV', '.MP3', '.FLAC')):
                    process_audio_file(full_audio_path)
        elif os.path.isfile(file_path):
            # Process a single audio file
            process_audio_file(file_path)
        else:
            print("The provided path is neither a file nor a directory, or the file format is not supported.")

    elif file_type == 'csv':
        interval_minutes = args.interval
        start_time = args.start
        end_time = args.end

        file_name = get_name(file_path)
        path = get_path(file_path)
        
        df = octave_band(file_path, start_time, end_time)
        plot_spectrogram_octave(path, df, file_name, interval_minutes, start_time, end_time)

if __name__ == "__main__":
    main()
