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
from zoneinfo import ZoneInfo


from audio_processing.common.git_version import get_stable_version
from audio_processing.common.filesystem import get_audiofiles,get_device_id
from audio_processing.common.paths import get_spl_output_dir

from audio_processing.spl.writers import write_leq_csv
from audio_processing.spl.PyOctaveBand_reduced import * 
from audio_processing.spl.models import AcousticLevelResult,ThirdOctaveResult,AcousticFileResult
from audio_processing.spl.spl_model import LeqLevelOctave
from audio_processing.spl.utils_acoustics import * 

from audio_processing.campaign.config import load_config


def run_leq_for_source(source,config,logger=None) -> Path | None:

    audio_path = Path(source.raw_data_path)
    audio_files = get_audiofiles(audio_path)

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
            valid_audio_files.append(audio_file)
        except Exception as exc:
            if logger:
                logger.warning("Error leyendo metadata de %s: %s",audio_file,exc)
    
    if not valid_audio_files: return None

    fs = int(np.median(sample_rates))
    rows=[]
    columns = ["LA","LC","LZ","LC-LA","LAmax","LAmin","filename","date"]

    for audio_file in tqdm.tqdm(valid_audio_files,desc = f'SPL {source.source_id}'):

        try:
            metadata = audio_metadata.load(audio_file)
            device_id = get_device_id(metadata)

            calibration = calibration_constants.get(device_id,calibration_constants.get("songmeter",-10.16))
            calculator = LeqLevelOctave(fs = fs,calibration_constant=calibration,window_size=fs,third_octave_fmax=config.spl.third_octave.fmax,third_octave_fmin=config.spl.third_octave.fmin)

            audio_data,_ = sf.read(audio_file)
            db_levels = calculator.calculate_spl_levels(audio_data)
            third_octave_levels = calculator.calculate_third_octave_levels(audio_data)

            combined_row = db_levels + third_octave_levels

            start_timestamp = timestamp_from_filename(audio_file)
            timestamps = [start_timestamp + datetime.timedelta(seconds=i) for i in range(combined_row.shape[0])]

            for row,timestamp in zip(combined_row,timestamps): rows.append(list(row) + [audio_file.name,timestamp.strftime("%Y-%m-%d %H:%M:%S")])

        except Exception as e:
            if logger: logger.warning(f"Error procesando {audio_file}: {e}")
    
    if not rows: return None

    output_dir = get_spl_output_dir(source,config)

    output_path = (output_dir / f"leq_{source.source_id}.csv")

    return write_leq_csv( rows = rows, columns = columns, output_path = output_path)


def run_leq_for_file(audio_file: Path, calibration_constants: dict, config,logger=None) -> list[AcousticLevelResult]:

    audio_file = Path(audio_file)

    try:

        metadata = audio_metadata.load(audio_file)
        fs = int(metadata.streaminfo.sample_rate)
        device_id = get_device_id(metadata)
        
        calibration = calibration_constants.get(device_id,calibration_constants.get("songmeter",-10.16))

        calculator = LeqLevelOctave(
            fs                      = fs,
            calibration_constant    = calibration,
            window_size             = fs,
            third_octave_fmin       = config.spl.third_octave.fmin,
            third_octave_fmax       = config.spl.third_octave.fmax)
        

        audio_data, _ = sf.read(audio_file)
        db_levels = calculator.calculate_spl_levels(audio_data)
        start_timestamp = timestamp_from_filename(audio_file)

        if start_timestamp.tzinfo is None: start_timestamp = start_timestamp.replace(tzinfo=ZoneInfo(config.campaign.timezone))

        results: list[AcousticLevelResult] = []

        for index,row in enumerate(db_levels):

            la_db,lc_db,lz_db,lc_la_db,la_max_db,la_min_db = row

            result = AcousticLevelResult(
                timestamp           = start_timestamp + datetime.timedelta(seconds = index),
                la_db               = float(la_db),
                lc_db               = float(lc_db),
                lz_db               = float(lz_db),
                lc_la_db            = float(lc_la_db),
                la_max_db           = float(la_max_db),
                la_min_db           = float(la_min_db),
                aggregation_seconds = 1.0
            )

            results.append(result)

        return results

    except Exception as e:

        if logger: logger.exception(f"Error procesando SPL de {audio_file}")
        raise



def run_third_octave_for_file(audio_file: Path, calibration_constants: dict, config, logger=None) -> list[ThirdOctaveResult]:

    audio_file = Path(audio_file)

    try:

        metadata            = audio_metadata.load(audio_file)
        fs                  = int(metadata.streaminfo.sample_rate)
        device_id           = get_device_id(metadata)
        calibration         = calibration_constants.get(device_id,calibration_constants.get("songmeter",-10.16))
        third_octave_fmin   = config.spl.third_octave.fmin
        third_octave_fmax   = config.spl.third_octave.fmax
        audio_data, _       = sf.read(audio_file)
        start_timestamp     = timestamp_from_filename(audio_file)
        results:             list[ThirdOctaveResult] = []

        
        if start_timestamp.tzinfo is None: start_timestamp  = start_timestamp.replace(tzinfo=ZoneInfo(config.campaign.timezone))
            
        calculator = LeqLevelOctave(
            fs                      = fs,
            calibration_constant    = calibration,
            window_size             = fs,
            third_octave_fmin       = third_octave_fmin,
            third_octave_fmax       = third_octave_fmax
        )

        
        levels, frequencies = calculator.calculate_third_octave_levels(audio_data)

        for index,row in enumerate(levels):

            bands_db = { normalize_third_octave_band(float(frequency)) : float(level) for frequency,level in zip(frequencies,row) }
            
            results.append(
                ThirdOctaveResult(
                    timestamp           = (start_timestamp + datetime.timedelta(seconds=index)),
                    aggregation_seconds = 1.0,
                    bands_db            = bands_db)
            )

        return results

    except Exception as e:
        if logger: logger.exception(f"Error calculando tercios de octava para: {audio_file}")
        raise


                

def run_acoustic_for_file(audio_file:Path,calibration_constants: dict, config,logger=None) -> AcousticLevelResult:

    audio_file = Path(audio_file)

    try:

        metadata                    = audio_metadata.load(audio_file)
        fs                          = int(metadata.streaminfo.sample_rate)
        device_id                   = get_device_id(metadata)
        calibration                 = calibration_constants.get(device_id,calibration_constants.get("songmenter",-10,16))
        start_timestamp             = timestamp_from_filename(audio_file)
        levels_results:             list[AcousticLevelResult] = []
        thirds_results:             list[ThirdOctaveResult] = []
        third_octave_fmin           = config.spl.third_octave.fmin
        third_octave_fmax           = config.spl.third_octave.fmax
        audio_data                  = sf.read(audio_file)
        
        calculator = LeqLevelOctave(
            fs                      = fs,
            calibration_constant    = calibration,
            window_size             = fs,
            third_octave_fmin       = third_octave_fmin,
            third_octave_fmax       = third_octave_fmax,
        )

        if start_timestamp.tzinfo is None: start_timestamp = start_timestamp.replace(tzinfo=ZoneInfo(config.campaign.timezone))

        
        db_levels = calculator.calculate_spl_levels(audio_data)
        
        
        for index,row in enumerate(db_levels):

            la_db,lc_db,lz_db,lc_la_db,la_max_db,la_min_db = row

            levels_results.append(
                AcousticLevelResult(
                    timestamp           = start_timestamp + datetime.timedelta(seconds = index),
                    la_db               = float(la_db),
                    lc_db               = float(lc_db),
                    lz_db               = float(lz_db),
                    lc_la_db            = float(lc_la_db),
                    la_max_db           = float(la_max_db),
                    la_min_db           = float(la_min_db),
                    aggregation_seconds = 1.0
            ))


        if config.spl.third_octave.enabled: 

            levels, frequencies = calculator.calculate_third_octave_levels(audio_data)

            for index,row in enumerate(levels):

                bands_db = { normalize_third_octave_band(float(frequency)):float(level) for frequency,level in zip(frequencies,row)}
                
                thirds_results.append(
                    ThirdOctaveResult(
                        timestamp               = start_timestamp + datetime.timedelta(seconds=index),
                        aggregation_seconds     = 1.0,
                        bands_db                = bands_db
                ))
    except Exception as e:
        logger.error(f"Error procesando el archivo {audio_file}")
        raise

    
    return AcousticFileResult( levels=levels_results, third_octaves=thirds_results )



        

            




