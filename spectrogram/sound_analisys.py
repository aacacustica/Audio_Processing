# some changes here
import os
import sys
import numpy as np
import matplotlib.pyplot as plt
from scipy.fft import fft
import soundfile as sf
from scipy.signal import spectrogram
import librosa

def plot_waveform(audio_file, output_dir):
    # Read the audio file
    data, samplerate = sf.read(audio_file)

    # Normalize to 16-bit range
    data = data / np.max(np.abs(data))

    # Time axis (for plotting)
    time = np.arange(len(data)) / samplerate

    # Plot waveform
    plt.figure(figsize=(10, 5))
    plt.plot(time, data, color='blue')
    plt.title(f"Waveform of {os.path.basename(audio_file)}")
    plt.xlabel("Time (seconds)")
    plt.ylabel("Amplitude")

    # Set the x-axis limits to exactly cover the data range
    plt.xlim([time[0], time[-1]])

    # Save the plot
    plt.savefig(os.path.join(output_dir, "waveform_" + os.path.basename(audio_file) + ".png"))
    plt.close()


def plot_spectrum(audio_file, output_dir, n_fft=2048):
    # Read the audio file
    data, samplerate = sf.read(audio_file)

    # Normalize to 16-bit range
    data = data / np.max(np.abs(data))

    # Ensure that length of data is a multiple of n_fft by zero-padding
    data_padded = np.pad(data, (0, n_fft - len(data) % n_fft), 'constant')

    # Fast Fourier Transform
    fft_result = fft(data_padded, n=n_fft)
    
    # Compute absolute value of FFT (to get magnitude) and normalize
    spectrum = np.abs(fft_result) / len(fft_result)

    # Frequency axis (for plotting)
    freq = np.linspace(0, samplerate, len(spectrum))

    # Convert spectrum to dB
    spectrum_db = 20 * np.log10(spectrum[:len(freq)//2])

    # Print audio info
    print(f"\n\nProcessing {audio_file}:")
    print(f"Sample rate (fs): {samplerate} Hz")
    print(f"Duration: {len(data) / samplerate} seconds")

    # Plot only up to Nyquist frequency
    plt.figure(figsize=(10, 5))
    plt.plot(freq[:len(freq)//2], spectrum_db, color='blue')
    plt.title(f"Spectrum of {os.path.basename(audio_file)}")
    plt.xlabel("Frequency (Hz)")
    plt.ylabel("Magnitude (dB)")

    # Set the x-axis limits to exactly cover the data range
    plt.xlim([freq[0], freq[len(freq)//2 - 1]])

    # Desired range of dB values for display
    desired_range_start = 30
    desired_range_end = 100
    desired_range = desired_range_end - desired_range_start

    # Calculate the existing range of dB values in the data
    original_range = np.max(spectrum_db) - np.min(spectrum_db)

    # Calculate the factor to linearly map the original range to the desired range
    mapping_factor = original_range / desired_range

    # Set the y-ticks for the plot
    plt.yticks(np.linspace(np.min(spectrum_db), np.max(spectrum_db), 8))  # 8 ticks

    # Calculate the corresponding dB values for the y-ticks in the desired range and set them as the tick labels
    plt.gca().set_yticklabels((desired_range_start + (plt.gca().get_yticks() - np.min(spectrum_db)) / mapping_factor).astype(int))

    # Save the plot
    plt.savefig(os.path.join(output_dir, "spectrum_" + os.path.basename(audio_file) + ".png"))
    plt.close()



# def plot_spectrogram(audio_file, output_dir):
#     # Read the audio file
#     data, samplerate = sf.read(audio_file)

#     # Normalize to 16-bit range
#     data = data / np.max(np.abs(data))

#     # Compute spectrogram
#     f, t, Sxx = spectrogram(data, samplerate)

#     # Plot spectrogram
#     plt.figure(figsize=(10, 5))
#     plt.pcolormesh(t, f, 10 * np.log10(Sxx), shading='gouraud', cmap='hot')
#     plt.title(f"Spectrogram of {os.path.basename(audio_file)}")
#     plt.xlabel("Time (seconds)")
#     plt.ylabel("Frequency (Hz)")
#     plt.colorbar(label="")
    
#     # Set y limit to half the sample rate (Nyquist frequency)
#     plt.ylim(0, samplerate / 2)
    
#     # Save the plot
#     plt.savefig(os.path.join(output_dir, "spectrogram_" + os.path.basename(audio_file) + ".png"))
#     plt.close()

def plot_spectrogram(audio_file, output_dir):
    # Read the audio file
    data, samplerate = sf.read(audio_file)

    # Normalize to 16-bit range
    data = data / np.max(np.abs(data))

    # Compute spectrogram
    f, t, Sxx = spectrogram(data, samplerate)

    # Convert to dB
    Sxx_db = 10 * np.log10(Sxx)

    # Plot spectrogram
    plt.figure(figsize=(10, 5))
    img = plt.pcolormesh(t, f, Sxx_db, shading='gouraud', cmap='hot')
    plt.title(f"Spectrogram of {os.path.basename(audio_file)}")
    plt.xlabel("Time (seconds)")
    plt.ylabel("Frequency (Hz)")

    # Set y limit to half the sample rate (Nyquist frequency)
    plt.ylim(0, samplerate / 2)
    
    # Create colorbar and specify its label
    cbar = plt.colorbar(img)
    cbar.set_label("Magnitude (dB)")

    # Calculate the existing range of dB values in the data
    original_range = img.get_clim()[1] - img.get_clim()[0]

    # Desired range of dB values for display
    desired_range_start = 30
    desired_range_end = 100
    desired_range = desired_range_end - desired_range_start

    # Calculate the factor to linearly map the original range to the desired range
    mapping_factor = original_range / desired_range

    # Set the ticks for the colorbar
    cbar.set_ticks(np.linspace(img.get_clim()[0], img.get_clim()[1], 8))  # 8 ticks

    # Calculate the corresponding dB values for the ticks in the desired range and set them as the tick labels
    cbar.set_ticklabels((desired_range_start + (cbar.get_ticks() - img.get_clim()[0]) / mapping_factor).astype(int))

    # Save the plot
    plt.savefig(os.path.join(output_dir, "spectrogram_" + os.path.basename(audio_file) + ".png"))
    plt.close()

def plot_melspectrogram(audio_file, output_dir, n_fft=2048, hop_length=512, n_mels=128):
    # Read the audio file
    data, samplerate = sf.read(audio_file)

    # Normalize to 16-bit range
    data = data / np.max(np.abs(data))

    # Compute mel spectrogram
    S = librosa.feature.melspectrogram(data, sr=samplerate, n_fft=n_fft, hop_length=hop_length, n_mels=n_mels)

    # Convert to dB
    S_db = librosa.power_to_db(S, ref=np.max)

    # Plot mel spectrogram
    plt.figure(figsize=(10, 5))
    img = plt.imshow(S_db, origin='lower', aspect='auto', cmap='hot')
    plt.title(f"Mel spectrogram of {os.path.basename(audio_file)}")
    plt.xlabel("Time (frames)")
    plt.ylabel("Mel frequency bins")

    # Create colorbar and specify its label
    cbar = plt.colorbar(img)
    cbar.set_label("Magnitude (dB)")

    # Save the plot
    plt.savefig(os.path.join(output_dir, "melspectrogram_" + os.path.basename(audio_file) + ".png"))
    plt.close()
    
    

def process_directory(input_dir):
    # Create output directory
    output_dir = "plots_" + os.path.basename(input_dir)
    os.makedirs(output_dir, exist_ok=True)

    # Go through all files in the input directory
    for filename in os.listdir(input_dir):
        # Check if the file is an audio file (you can add more formats if needed)
        if filename.endswith(".wav") or filename.endswith(".flac"):
            # Full path to the audio file
            audio_file = os.path.join(input_dir, filename)
            # Plot and save the waveform, spectrum, spectrogram and melspectrogram
            plot_waveform(audio_file, output_dir)
            plot_spectrum(audio_file, output_dir)
            plot_spectrogram(audio_file, output_dir)
            plot_melspectrogram(audio_file, output_dir)



# Get the input directory from the command line arguments
input_dir = sys.argv[1]
process_directory(input_dir)
