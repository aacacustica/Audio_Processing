import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import butter, lfilter, freqz

fs = 48000 
duration = 2  # seconds

#bandpass filter
def bandpass_filter(data, lowcut, highcut, fs, order=5):
    nyq = 0.5 * fs
    low = lowcut / nyq
    high = highcut / nyq
    b, a = butter(order, [low, high], btype='band')
    y = lfilter(b, a, data)
    return y

#sum of two sine waves
t = np.linspace(0, duration, int(fs * duration), endpoint=False)
signal = 0.5 * (np.sin(2 * np.pi * 500 * t) + np.sin(2 * np.pi * 1500 * t))
# octave bands
octave_bands = [100, 125, 160, 200, 250, 315, 400, 500, 630, 800, 1000, 1250, 1600, 2000, 2500, 3150, 4000, 5000, 6300, 8000, 10000]


bands = {}
for i in range(len(octave_bands)-1):
    lowcut = octave_bands[i]
    highcut = octave_bands[i+1]
    filtered_signal = bandpass_filter(signal, lowcut, highcut, fs)
    bands[f"{lowcut}-{highcut} Hz"] = filtered_signal


#####################
#  PLOTTING RESULTS #
plt.figure(figsize=(12, 6))
for band, filtered_signal in bands.items():
    power = np.sqrt(np.mean(filtered_signal**2))
    plt.bar(band, power, width=1)

plt.ylabel('Amplitude')
plt.xlabel('Frequency Bands')
plt.title('1/3 Octave Band Equalizer')
plt.xticks(rotation=90)
plt.tight_layout()
plt.show()
