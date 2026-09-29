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


class LeqLevelOctave:
    def __init__(self, fs:int, calibration_constant:float, window_size:int,third_octave_fmin: float,third_octave_fmax: float):
        self.fs = fs
        self.C = calibration_constant
        self.window_size = window_size
        self.bA, self.aA = a_weighting_coeffs_design(fs)
        self.bC, self.aC = c_weighting_coeffs_design(fs)
        self.fast_samples = int(window_size / 8)
        self.fmin_octaves = third_octave_fmin
        self.fmax_octaves = third_octave_fmax

        logging.info(f"LeqLevelOctave calculator initialized with fs: {fs}, C: {calibration_constant}, window_size: {window_size}, fmin octaves: {third_octave_fmin}, fmax octaves: {third_octave_fmax}")


    def calculate_spl_levels(self, audio_data):
        
        db_levels = []
        
        for fstart in range(0, len(audio_data) - self.window_size + 1, self.window_size):
            
            frame = audio_data[fstart:fstart + self.window_size]
            yA = lfilter(self.bA, self.aA, frame)
            yC = lfilter(self.bC, self.aC, frame)

            LA = get_db_level(yA, self.C)
            LC = get_db_level(yC, self.C)
            LZ = get_db_level(frame, self.C)

            fast_levels = [get_db_level(yA[idx:idx + self.fast_samples], self.C) for idx in range(0, len(frame) - self.fast_samples + 1, self.fast_samples)]
                           
            Lmax = np.max(fast_levels)
            Lmin = np.min(fast_levels)

            # getting the LC-LA difference
            LC_LA = LC - LA

            db_levels.append([LA, LC, LZ, LC_LA, Lmax, Lmin])

        return np.round(db_levels, 2)

    def calculate_third_octave_levels(self,audio_data) -> tuple[np.ndarray,np.ndarray]:

        all_levels = []
        frequencies = None

        fmin_octaves = self.fmin_octaves
        fmax_octaves = self.fmax_octaves
        calibration_coeff = self.C

        for fstart in range(0,len(audio_data) - self.window_size + 1, self.window_size):
            
            frame = audio_data[fstart:fstart + self.window_size]
            levels, freqs = third_octave_filter(frame,self.fs, order=6, limits=[fmin_octaves,fmax_octaves],show=0,sigbands=0,calibration_coeff=calibration_coeff)

            if frequencies is None: frequencies = np.asarray(freqs,dtype=float)

            all_levels.append(levels)

        
        if frequencies is None: return (np.empty((0,0)),np.empty(0))



        return (np.round(np.vstack(all_levels), 2),frequencies)