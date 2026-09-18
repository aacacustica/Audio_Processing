import numpy as np
import soundfile as sf
import pandas as pd

from pyfilterbank.splweighting import a_weighting_coeffs_design, c_weighting_coeffs_design
from scipy.signal import lfilter
from pathlib import Path

from audio_processing.spl.utils_acoustics import * 
from audio_processing.common.git_version import get_stable_version
from audio_processing.common.filesystem import get_audiofiles,get_device_id
from audio_processing.common.paths import get_spl_output_dir
from audio_processing.spl.writers import write_leq_csv
from audio_processing.spl.PyOctaveBand_reduced import * 
from audio_processing.campaign.config import load_config

config = load_config()


class LeqLevelOctave:
    def __init__(self, fs, calibration_constant, window_size):
        self.fs = fs
        self.C = calibration_constant
        self.window_size = window_size
        self.bA, self.aA = a_weighting_coeffs_design(fs)
        self.bC, self.aC = c_weighting_coeffs_design(fs)
        self.fast_samples = int(window_size / 8)
        self.fmin_octaves = config.spl.third_octaves.fmin
        self.fmax_octaves = config.spl.third_octaves.fmax

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

    def calculate_third_octave_levels(self,audio_data):

        fmin_octaves = self.fmin_octaves
        fmax_octaves = self.fmax_octaves

        freq_labels = None

        for fstart in range(0,len(audio_data) - self.window_size + 1, self.window_size):
            frame = audio_data[fstart:fstart + self.window_size]
            levels, freqs = third_octave_filter(frame,self.fs, order=6, limits=[fmin_octaves,fmax_octaves],show=0,sigbands=0)

            if freq_labels is None: freq_labels = [f"{round(freq, 1)}Hz" for freq in freqs]


        return np.round(levels, 2)