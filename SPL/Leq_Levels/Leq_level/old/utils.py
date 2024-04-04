
import numpy as np
import os
from pyfilterbank.octbank import FractionalOctaveFilterbank
from scipy.fft import fft
from pyfilterbank.octbank import frequencies_fractional_octaves
from scipy.signal import lfilter


# constantes de inicializacion
T = 1
#C = -54.70


def filterbanks(fs):
    """
    Create octave and third octave filterbanks object from pyfilterbank
    :param fs: Sample rate of the audio
    :return:
        third octave filterbank, octave filterbank
    """
    third_oct = FractionalOctaveFilterbank(
        sample_rate=fs,
        order=4,
        nth_oct=3.0,
        norm_freq=1000.0,
        start_band=-19,
        end_band=13,
        edge_correction_percent=0.01,
        filterfun='cffi')

    octave = FractionalOctaveFilterbank(
        sample_rate=fs,
        order=4,
        nth_oct=1.0,
        norm_freq=1000.0,
        start_band=-5,
        end_band=4,
        edge_correction_percent=0.01,
        filterfun='cffi')

    return third_oct, octave

def get_edge_frequencies(idx_low=-16,idx_high=12):
    "Return edge frequencies defined from the ISO 61260"
    G = 10**(3/10)
    fr = 1000
    b = 3
    idx = np.arange(-16,12)
    fm = G**(idx/b)*fr

    # upper and down freqs
    f_upper = fm*G**(1/(2*b))  
    f_lower = fm*G**(-1/(2*b))
    return f_lower, fm , f_upper

def parseval(x_dft):
    """Returns SPL level from a complex Spectrum"""
    n = len(x_dft)
    po = 0.000002
    x_mag = np.abs(x_dft)
    lp = 10*np.log10(np.sum(x_mag**2) / ((po**2)*(n**2)))
    return lp


def third_octave_dft(frame, f_lower, f_upper, fs, C):
    x_dft = fft(frame)
    k = np.arange(0,fs,fs/len(frame))
    band_levels = []
    
    for fl , fh in zip(f_lower, f_upper):
        idx_band = (k >= fl) & (k < fh)
        x_dft_band = x_dft[idx_band]
        lp = parseval(x_dft_band) + C
        band_levels.append(lp)
    
    return band_levels 

def db_level(x, T, C):
    """
    Get SPL from a time series vector

    :param x: pressure values history from audio
    :param T: Time constant
    :param C: Calibration constant
    :return: Sound pressure level
    """
    po = 0.000002
    level = 10 * np.log10(np.nansum((x / po) ** 2) / T) + C
    return level

def get_db_level(x, C):
    """
    Get SPL from a time series vector

    :param x: pressure values history from audio
    :param C: Calibration constant
    :return: Sound pressure level
    """
    pref = 0.000002
    level = 10*np.log10(np.mean(x**2)/pref**2) + C
    return level



def get_calibration_constant(x,db_value,T):
    """
    Obtain calibration constant from a reference audio, typically 1khz at 94 dB

    :param x: pressure values history from audio
    :param db_value: dB value of the reference audio
    :param T: Time constant
    :return: Calibration constant C
    """
    po = 0.000002
    level = 10 * np.log10(np.nansum((x / po) ** 2) / T)
    C = db_value - level
    return C

def leq(levels):
    """
    Get continous equivalent level from a aeries of Spl values

    :param levels: SPl levels to obtain Equivalent sound pressure level
    :return: Leq level
    """
    e_sum = (np.sum(np.power(10, np.multiply(0.1, levels)))) / len(levels)
    eq_level = 10 * np.log10(e_sum)
    return eq_level


def get_oct_levels(y,octave,C):
    """

    :param y: Audio values
    :param octave: octave filterbank object
    :return: SPL level in each octave
    """
    y_oct, _ = octave.filter(y)
    oct_level = [get_db_level(f, C) for f in y_oct.T]
    return oct_level


def get_audiofiles(path):
    """

    Get audiofiles paths of all audio files in a dir

    :param path: path to look for audios
    :return: list of paths of audio files
    """
    #funcion que carga los archivos wav en una lista de python
    files = os.listdir(path) # listar los nombres de archivos que estan dentro del directorio
    audiofiles = [os.path.join(path,f) for f in files if f.endswith('.wav')] # verificar si son .wav y añadirlos las rutas a una lista
    return audiofiles

