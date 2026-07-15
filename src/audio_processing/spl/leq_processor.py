import logging
import tqdm
import audio_metadata
import os
import datetime

import numpy as np
import soundfile as sf
import pandas as pd

from pyfilterbank.splweighting import a_weighting_coeffs_design, c_weighting_coeffs_design
from scipy.signal import lfilter
from pathlib import Path

from audio_processing.acoustics.levels import get_db_level
from audio_processing.acoustics.calibration import read_calibration_constants
from audio_processing.common.git_version import get_stable_version
from audio_processing.common.filesystem import get_audiofiles,get_device_id
from audio_processing.common.paths import get_spl_output_dir
from audio_processing.spl.writers import write_leq_csv

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

def _get_audiofiles(path: Path) -> list[Path]:

    return sorted(file for file in path.iterdir() if file.is_file() and file.suffix.lower() == '.wav')

def _get_device_id(metadata) -> str:

    artists_tags = metadata.tags.get('artist',['songmeter'])

    if not artists_tags: return 'songmeter'

    parts = artists_tags[0].split(" ")

    if len(parts) < 2: return 'songmenter'

    return parts[1].lower()

def _timestamp_from_filename(path: Path) -> datetime.datetime:

    return datetime.datetime.strptime(path.stem, "%Y%m%d_%H%M%S")
        
def run_leq_for_source(source,config,logger=None) -> Path | None:

    audio_path = Path(source.raw_data_path)
    audio_files = _get_audiofiles(audio_path)

    if not audio_files:
        if logger: logger.warning("No hay archivos WAV en %s",audio_path)
        return None
    
    calibration_file = Path(config.spl.calibration_file)

    if not calibration_file.is_absolute(): calibration_file = (Path(config._config_dir) / calibration_file)

    calibration_constants = read_calibration_constants(calibration_file)

    sample_rates = []
    valid_audio_files = []

    for audio_file in audio_files:
        try:
            metadata = audio_metadata.load(audio_file)
            sample_rates.append(metadata.streaminfo.sample_rate)
            valid_audio_files.append(audio_files)
        except Exception as exc:
            if logger:
                logger.warning("Error leyendo metadata de %s: %s",audio_file,exc)
    
    if not valid_audio_files: return None

    fs = int(np.median(sample_rates))
    rows=[]
    columns = ["LA","LC","LZ","LC-LA","LAmax","LAmin","filename","date"]

    for audio_file in tqdm(valid_audio_files,desc = f'SPL {source.source_id}'):

        try:
            metadata = audio_metadata.load(audio_file)
            device_id = _get_device_id(metadata)

            calibration = calibration_constants.get(device_id,calibration_constants.get("songmeter",-10.16))
            calculator = LeqLevelOctave(fs = fs,calibration_constant=calibration,window_size=fs)

            audio_data,_ = sf.read(audio_file)
            db_levels = calculator.calculate_spl_levels(audio_data)

            start_timestamp = _timestamp_from_filename(audio_file)
            timestamps = [start_timestamp + datetime.timedelta(seconds=i) for i in range(db_levels.shape[0])]

            for row,timestamp in zip(db_levels,timestamps): rows.append(list(row) + [audio_file.name,timestamp.strftime("%Y-%m-%d %H:%M:%S")])

        except Exception as e:
            if logger: logger.warning(f"Error procesando {audio_file}: {e}")
    
    if not rows: return None

    output_dir = get_spl_output_dir(source,config)

    output_path = (output_dir / f"leq_{source.source_id}.csv")

    return write_leq_csv( rows = rows, columns = columns, output_path = output_path)

                

