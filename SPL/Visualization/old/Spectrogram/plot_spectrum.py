import os
import sys
import numpy as np
import matplotlib.pyplot as plt
from scipy.fft import fft
import soundfile as sf

def plot_spectrum(audio_file, output_dir):
    # Read the audio file
    data, samplerate = sf.read(audio_file)

    # Normalize to 16-bit range
    data = data / np.max(np.abs(data))

    # Fast Fourier Transform
    fft_result = fft(data)
    
    # Compute absolute value of FFT (to get magnitude) and normalize
    spectrum = np.abs(fft_result) / len(fft_result)

    # Frequency axis (for plotting)
    freq = np.linspace(0, samplerate, len(spectrum))

    # Print audio info
    print(f"Processing {audio_file}:")
    print(f"Sample rate (fs): {samplerate} Hz")
    print(f"Duration: {len(data) / samplerate} seconds")

    # Plot only up to Nyquist frequency
    plt.figure(figsize=(10, 5))
    plt.plot(freq[:len(freq)//2], 20 * np.log10(spectrum[:len(freq)//2]), color='blue')
    plt.title(f"Frequency Spectrum of {os.path.basename(audio_file)}")
    plt.xlabel("Frequency (Hz)")
    plt.ylabel("Magnitude (dB)")
    
    # Save the plot
    plt.savefig(os.path.join(output_dir, os.path.basename(audio_file) + ".png"))
    plt.close()

def process_directory(input_dir):
    # Create output directory
    output_dir = "spectro_" + os.path.basename(input_dir)
    os.makedirs(output_dir, exist_ok=True)

    # Go through all files in the input directory
    for filename in os.listdir(input_dir):
        # Check if the file is an audio file (you can add more formats if needed)
        if filename.endswith(".wav") or filename.endswith(".WAV"):
            # Full path to the audio file
            audio_file = os.path.join(input_dir, filename)
            # Plot and save the spectrum
            plot_spectrum(audio_file, output_dir)

# Get the input directory from the command line arguments
input_dir = sys.argv[1]
process_directory(input_dir)
