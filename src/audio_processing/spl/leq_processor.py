import numpy as np
import logging

from pyfilterbank.splweighting import a_weighting_coeffs_design, c_weighting_coeffs_design
from scipy.signal import lfilter

from audio_processing.acoustics.levels import get_db_level

class LeqLevelOctave:
    def __init__(self, fs, calibration_constant, window_size):
        self.fs = fs
        self.C = calibration_constant
        self.window_size = window_size
        self.bA, self.aA = a_weighting_coeffs_design(fs)
        self.bC, self.aC = c_weighting_coeffs_design(fs)
        self.fast_samples = int(window_size / 8)
        logging.info(f"LeqLevelOctave initialized with fs: {fs}, C: {calibration_constant}, window_size: {window_size}")


    def calculate_spl_levels(self, audio_data):
        db_levels = []
        for fstart in range(0, len(audio_data) - self.window_size + 1, self.window_size):
            frame = audio_data[fstart:fstart + self.window_size]
            yA = lfilter(self.bA, self.aA, frame)
            yC = lfilter(self.bC, self.aC, frame)

            LA = get_db_level(yA, self.C)
            LC = get_db_level(yC, self.C)
            LZ = get_db_level(frame, self.C)

            fast_levels = [get_db_level(yA[idx:idx + self.fast_samples], self.C)
                           for idx in range(0, len(frame) - self.fast_samples + 1, self.fast_samples)]
            Lmax = np.max(fast_levels)
            Lmin = np.min(fast_levels)

            # getting the LC-LA difference
            LC_LA = LC - LA

            db_levels.append([LA, LC, LZ, LC_LA, Lmax, Lmin])
        return np.round(db_levels, 2)