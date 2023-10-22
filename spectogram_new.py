import numpy as np
import matplotlib.pyplot as plt
import librosa
import librosa.display
import argparse
import os

def plot_spectrogram(y, sr, hop_length, n_fft):
    D = librosa.amplitude_to_db(np.abs(librosa.stft(y, n_fft=n_fft, hop_length=hop_length)), ref=np.max)

    plt.figure(figsize=(10, 4))
    librosa.display.specshow(D, sr=sr, x_axis='time', y_axis='log', hop_length=hop_length)
    plt.colorbar(format='%+2.0f dB')
    plt.title('Spectrogram')
    plt.tight_layout()
    plt.show()

def check_and_process(file_folder):
    if os.path.isfile(file_folder):
        try:
            y, sr = librosa.load(file_folder, sr=None)
            plot_spectrogram(y, sr, hop_length=512, n_fft=2048)
        except Exception as e:
            print(f"Error processing file {file_folder}: {e}")

    elif os.path.isdir(file_folder):
        files = os.listdir(file_folder)
        files = [file for file in files if file.endswith('.wav') or file.endswith('.WAV')]
        for file in files:
            print(f"Plotting spectrogram for {file}")
            try:
                y, sr = librosa.load(os.path.join(file_folder, file), sr=None)
                plot_spectrogram(y, sr, hop_length=512, n_fft=2048)
            except Exception as e:
                print(f"Error processing file {file}: {e}")
    else:
        print(f"{file_folder} is neither a valid file nor a directory.")

def argument_parser():
    parser = argparse.ArgumentParser(
        description="Plot spectrogram for a given audio file or folder",
        )
    parser.add_argument('-f', '--file_folder', help='Path to audio file or folder', required=True)
    return parser.parse_args()

if __name__ == "__main__":
    args = argument_parser()
    check_and_process(args.file_folder)