import numpy as np


def get_db_level(x, C):
    """
    Args:
        x (numpy.ndarray): A multi-dimensional array of audio signal values.
        C (float): A calibration constant for the audio recording device.
        axis (int): The axis along which the means are computed. By default, it computes the mean over the last axis.

    Returns:
        numpy.ndarray or float: The Sound Pressure Level (SPL) of the given audio signal in decibels. If the input 'x' is a multi-dimensional array, then an array of SPL values is returned, otherwise a single float value is returned.

    """
    pref = 0.000002
    mean_square = np.mean(x ** 2)

    if mean_square <= 0: return -np.inf
    
    return 10 * np.log10(mean_square / pref ** 2) + C