import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import butter, lfilter
import sounddevice as sd

# constants
fs = 48000 
duration = 1  # seconds
n_samples = int(fs * duration)

# actave bands
octave_bands = [100, 125, 160, 200, 250, 315, 400, 500, 630, 800, 1000, 1250, 1600, 2000, 2500, 3150, 4000, 5000, 6300, 8000, 10000]

# aandpass filter
def bandpass_filter(data, lowcut, highcut, fs, order=5):
    nyq = 0.5 * fs
    low = lowcut / nyq
    high = highcut / nyq
    b, a = butter(order, [low, high], btype='band')
    y = lfilter(b, a, data)
    return y

def audio_callback(indata, frames, time, status):
    if status:
        print(status)
    indata = indata[:, 0]  # mono audio
    power_bands = []
    for i in range(len(octave_bands)-1):
        lowcut = octave_bands[i]
        highcut = octave_bands[i+1]
        filtered_signal = bandpass_filter(indata, lowcut, highcut, fs)
        power = np.sqrt(np.mean(filtered_signal**2))
        power_bands.append(power)
    plot_data(power_bands)

plt.ion()  #interactive mode
fig, ax = plt.subplots()
bars = ax.bar(range(len(octave_bands)-1), np.zeros(len(octave_bands)-1))
ax.set_ylim(0, 0.1)
ax.set_ylabel('Amplitude')
ax.set_xlabel('Frequency Bands')
ax.set_title('1/3 Octave Band Equalizer')
ax.set_xticks(range(len(octave_bands)-1))
ax.set_xticklabels([f"{octave_bands[i]}-{octave_bands[i+1]} Hz" for i in range(len(octave_bands)-1)], rotation=90)

# update plot
def plot_data(power_bands):
    for bar, power in zip(bars, power_bands):
        bar.set_height(power)
    fig.canvas.draw()
    fig.canvas.flush_events()

# audio stream
with sd.InputStream(callback=audio_callback, channels=1, samplerate=fs, blocksize=n_samples):
    plt.show(block=True)
