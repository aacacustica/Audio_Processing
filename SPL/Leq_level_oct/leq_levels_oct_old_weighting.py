"""
leq_levels_oct_sos.py

Goal:
- NO SciPy / NO pyfilterbank at runtime (sensor side)
- Uses:
  - lfilter_np for A/C weighting (b,a loaded from YAML)
  - sosfilt_np for 1/3-oct bandpass bank (SOS loaded from YAML)
  - numpy + soundfile + yaml + audio_metadata

Files you need next to this script:
- lfilter_numpy.py   (contains lfilter_np)
- sosfilt_numpy.py   (contains sosfilt_np)
- weighting_fs<FS>.yaml
- sos_bank_1_3_fs<FS>.yaml
- calibration_constants.ini
"""






import soxr
import os
import sys
import datetime
import argparse
import configparser
import logging

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DEPS_DIR = os.path.join(BASE_DIR,'libs_c')
sys.path.insert(0,DEPS_DIR)


import leq_levels_oct_weighting_C as m

import numpy as np
import pandas as pd
import soundfile as sf
import yaml
import audio_metadata
from tqdm import tqdm

from lfilter_numpy import lfilter_np
from sosfilt_numpy import sosfilt_np

# If you still want to use these utils, make sure YOUR utils.py DOES NOT import scipy/pyfilterbank.
# This script only uses get_audiofiles + get_stable_version; both can be replaced easily if needed.
from utils import get_audiofiles, get_stable_version,twenty_db_fix


# -----------------------------
# Logging
# -----------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    filename="leq_level_1_3_oct.log",
    filemode="w",
)


PREF = 2e-6

# -----------------------------
# Small helpers
# -----------------------------
def get_level_db(x: np.ndarray, C: float) -> float:
    """SPL-like level in dB using mean-square reference to PREF."""
    x = np.asarray(x, dtype=np.float64)
    ms = float(np.mean(x * x)) + 1e-30
    return 10.0 * np.log10(ms / (PREF * PREF)) + float(C)


def read_calibration_constants(ini_file: str) -> dict:
    cfg = configparser.ConfigParser()
    cfg.read(ini_file)
    logging.info(f"Reading calibration constants from {ini_file}")
    return {k: float(v) for k, v in cfg["CalibrationConstants"].items()}


def get_device_id(metadata) -> str:
    artist_tags = metadata.tags.get("artist", ["songmeter"])
    if not artist_tags or len(artist_tags[0].split(" ")) < 2:
        return "songmeter"
    device_id = artist_tags[0].split(" ")[1].lower()
    logging.info(f"Device ID: {device_id}")
    return device_id


def find_audiomoth_folders(base_path: str):
    """Recursively find all subdirectories containing an 'AUDIOMOTH' folder."""
    for root, dirs, _files in os.walk(base_path):
        if "AUDIOMOTH" in dirs:
            yield root


def load_yaml(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def parse_arguments():
    parser = argparse.ArgumentParser(description="Calculate SPL + 1/3-octave levels without SciPy runtime")
    parser.add_argument("-p", "--path", type=str, required=True, help="Directory to be processed")
    parser.add_argument("--fs", type=int, default=None, help="Force FS (if metadata not reliable)")
    parser.add_argument("--weighting-yaml", type=str, default=None, help="Path to weighting_fsXXXX.yaml")
    parser.add_argument("--bank-yaml", type=str, default=None, help="Path to sos_bank_1_3_fsXXXX.yaml")
    parser.add_argument("--limit-folders", type=int, default=1, help="Process only first N folders (debug)")
    parser.add_argument("--limit-files", type=int, default=None, help="Process only first N wav files (debug)")
    return parser.parse_args()


# -----------------------------
# Core class
# -----------------------------
class LeqLevelOct:
    def __init__(
        self,
        fs: int,
        calibration_constant: float,
        window_size: int,
        audio_path: str,
        weighting_yaml_path: str,
        bank_yaml_path: str,
    ):
        self.fs = int(fs)
        self.C = float(calibration_constant)
        self.window_size = int(window_size)
        self.audio_path = audio_path

        # Load weighting (b,a) for A/C
        w = load_yaml(weighting_yaml_path)
        if int(w["fs"]) != self.fs:
            raise ValueError(f"Weighting YAML fs={w['fs']} does not match fs={self.fs}")

        self.bA = np.asarray(w["A_weighting"]["b"], dtype=np.float32)
        self.aA = np.asarray(w["A_weighting"]["a"], dtype=np.float32)
        self.bC = np.asarray(w["C_weighting"]["b"], dtype=np.float32)
        self.aC = np.asarray(w["C_weighting"]["a"], dtype=np.float32)

        # Load 1/3-oct SOS bank
        b = load_yaml(bank_yaml_path)
        if int(b["fs"]) != self.fs:
            raise ValueError(f"Bank YAML fs={b['fs']} does not match fs={self.fs}")

        self.sos_bank = b["sos_bank"]              # list[band] -> list[section] -> 6 floats
        self.center_freqs = b["freq_center"]       # for column labels

        logging.info(
            f"LeqLevelOct initialized fs={self.fs}, C={self.C}, window={self.window_size}, "
            f"bands={len(self.sos_bank)}"
        )

    def process_audio_files(self, audio_files):
        """
        Returns:
          all_data: list of per-file rows
          col_names: column names
        """
        col_names = ["LA", "LC", "LZ", "LAmax", "LAmin"] + \
                    [f"{f:.2f}Hz" for f in self.center_freqs] + \
                    ["filename", "date"]

        all_data = []

        for audio_file in audio_files:
            db = []

            x, fs_read = sf.read(os.path.join(self.audio_path, audio_file))
            if x.ndim > 1:
                x = x[:, 0]
            x = np.asarray(x, dtype=np.float32).ravel()
            if len(x) < self.window_size:
                logging.warning(f"Skipping {audio_file}: shorter than one window.")
                continue
            
            if fs_read != self.fs:
                logging.warning(f"File {audio_file} has fs={fs_read} but expected {self.fs}. Resampling audio file")
                x = soxr.resample(x,in_rate = fs_read,out_rate=self.fs).astype(np.float32,copy=False)
                logging.info(f"Resampled file {audio_file} into fs={self.fs} ")

            name_split = os.path.splitext(audio_file)[0]
            start_timestamp = datetime.datetime.strptime(name_split, "%Y%m%d_%H%M%S")

            frame_starts = range(0, len(x) - self.window_size + 1, self.window_size)
            timestamps = [
                start_timestamp + datetime.timedelta(seconds=fstart / self.fs)
                for fstart in frame_starts
            ]

            # Streaming states (per file)
            ziA = None
            ziC = None
            ziBands = [None] * len(self.sos_bank)
            #---C++ implementation substitution----
            for fstart, timestamp in zip(frame_starts, timestamps):
                frame = x[fstart:fstart + self.window_size]
                
                # A/C weighting via lfilter_np (b,a)
                #yA, ziA = lfilter_np(self.bA, self.aA, frame, zi=ziA)
                #yC, ziC = lfilter_np(self.bC, self.aC, frame, zi=ziC)

                self.bA = np.ascontiguousarray(self.bA, dtype=np.float32)
                self.aA = np.ascontiguousarray(self.aA, dtype=np.float32)
                frame   = np.ascontiguousarray(frame, dtype=np.float32)

                if ziA is not None:
                    ziA = np.ascontiguousarray(ziA, dtype=np.float32)

                yA, ziA  = m.lfilter_np(self.bA, self.aA, frame, ziA)
                yC, ziC  = m.lfilter_np(self.bC, self.aC, frame, ziC)

                


                #LA = round(get_level_db(yA, self.C), 2)
                #LC = round(get_level_db(yC, self.C), 2)
                #LZ = round(get_level_db(frame, self.C), 2)

                LA = round(float(m.get_level_db(yA, self.C)),2)
                LC = round(float(m.get_level_db(yC, self.C)),2)
                LZ = round(float(m.get_level_db(frame, self.C)),2)
                # LAmax/LAmin over FAST subchunks (8 per second if window=fs)

                fast_chunk = self.window_size // 8
                fast_levels = [
                    #get_level_db(yA[i:i + fast_chunk], self.C)
                    float(m.get_level_db(yA[i:i + fast_chunk], self.C))
                    for i in range(0, len(yA) - fast_chunk + 1, fast_chunk)
                ]
                Lmax = round(float(np.max(fast_levels)), 2)
                Lmin = round(float(np.min(fast_levels)), 2)

                # 1/3-oct band levels via SOS bank
                band_levels = []

                for i, sos in enumerate(self.sos_bank):
                    sos = np.asarray(sos, dtype=np.float32)
                    sos = np.ascontiguousarray(sos,dtype = np.float32)
                    #yb, ziBands[i] = sosfilt_np(sos, frame, zi=ziBands[i])

                    

                    yb , ziBands[i] = m.sosfilt_np(sos,frame,zi=ziBands[i])
                    #band_levels.append(round(get_level_db(yb, self.C), 2))
                    band_levels.append(round(m.get_level_db(yb,self.C),2))

                #20db fix
                    band_levels = twenty_db_fix(band_levels)
                row = [LA, LC, LZ, Lmax, Lmin] + band_levels + [
                    audio_file,
                    timestamp.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
                ]
                db.append(row)

            if db:
                all_data.append(db)
                logging.info(f"Processed file: {audio_file} (rows={len(db)})")
            else:
                logging.warning(f"Processed file: {audio_file} produced 0 rows (no frames).")

        return all_data, col_names


# -----------------------------
# Main
# -----------------------------
def main():
    r"""
    Example:
      python leq_levels_oct_sos.py -p "\\192.168.205.117\AAC_Server\PUERTOS\NOISEPORT\20231211_SANTUR\3-Medidas\"
    """
    args = parse_arguments()
    #stable_version = get_stable_version()
    #--DEBUG--
    stable_version = "v0.1.0"
    base_path = args.path

    calibration_constants = read_calibration_constants("/home/aac/I+D/CODIGOS/Audio_Processing/SPL/Leq_level_oct/calibration_constants.ini")

    audiomoth_folders = list(find_audiomoth_folders(base_path))
    if args.limit_folders is not None:
        audiomoth_folders = audiomoth_folders[:args.limit_folders]

    for subfolder in tqdm(audiomoth_folders, desc="Processing folders"):
        logging.info(f"Processing audio files: {subfolder}...")
        audio_path = os.path.join(subfolder, "AUDIOMOTH")
        if not os.path.exists(audio_path):
            logging.warning(f"Skipping {subfolder}, AUDIOMOTH folder not found.")
            continue

        audio_files = get_audiofiles(audio_path)
        if not audio_files:
            logging.warning(f"No audio files found in: {audio_path}")
            continue

        # Read metadata to get sample rates (unless forced)
        sample_rates = []
        valid_audio_files = []

        logging.info("Reading metadata...")
        for file in tqdm(audio_files, desc="Reading metadata"):
            try:
                metadata = audio_metadata.load(os.path.join(audio_path, file))
                sample_rates.append(metadata.streaminfo.sample_rate)
                valid_audio_files.append(file)
            except Exception as e:
                logging.warning(f"Error reading file metadata: {file}, {e}")

        if not valid_audio_files:
            logging.warning(f"No valid audio files to process in {subfolder}")
            continue

        if args.limit_files is not None:
            valid_audio_files = valid_audio_files[:args.limit_files]

        if args.fs is not None:
            fs = int(args.fs)
        else:
            fs = int(round(float(np.median(sample_rates)))) if sample_rates else None

        if fs is None:
            logging.warning("Could not determine fs.")
            continue

        # Decide which YAMLs to load (either given or inferred)
        weighting_yaml = args.weighting_yaml or f"weighting_fs{fs}.yaml"
        bank_yaml = args.bank_yaml or f"sos_bank_1_3_fs{fs}.yaml"

        if not os.path.exists(weighting_yaml):
            raise FileNotFoundError(f"Missing weighting YAML: {weighting_yaml}")
        if not os.path.exists(bank_yaml):
            raise FileNotFoundError(f"Missing bank YAML: {bank_yaml}")

        logging.info(f"Using sample rate: {fs}")
        logging.info(f"Using weighting YAML: {weighting_yaml}")
        logging.info(f"Using bank YAML: {bank_yaml}")

        # Initialize calculator
        calculator = LeqLevelOct(
            fs=fs,
            calibration_constant=-10.16,
            window_size=fs,  # 1 second
            audio_path=audio_path,
            weighting_yaml_path=weighting_yaml,
            bank_yaml_path=bank_yaml,
        )

        all_data_subfolder = []

        logging.info(f"Processing {len(valid_audio_files)} files in {subfolder}...")
        
        for audio_file in tqdm(valid_audio_files, desc="Processing audio files"):
            try:
                filepath = os.path.join(audio_path, audio_file)
                metadata = audio_metadata.load(filepath)
                device_id = get_device_id(metadata)
                C = calibration_constants.get(device_id, -10.16)
                calculator.C = C

                file_data, col_names = calculator.process_audio_files([audio_file])
                all_data_subfolder.extend(file_data)

                logging.info(
                    f"Processed file: {audio_file} with device_id={device_id}, C={C}, fs={fs}"
                )
            except Exception as e:
                logging.warning(f"Error processing file: {audio_file}, {e}")

        # Save output
        if all_data_subfolder:
            
            flat_data = [row for file_rows in all_data_subfolder for row in file_rows]
            

            if not flat_data:
                logging.warning(f"No rows to save for folder {subfolder} (flat_data is empty). Skipping CSV.")
                continue

            df = pd.DataFrame(flat_data, columns=col_names)
            df = df.sort_values(by="date")
            
            folder_name = subfolder.split("\\")[-1]
            output_filename = f"leq_oct_{folder_name}_{stable_version}_sos_weighting.csv"
            #Testing
            output_path = os.path.join(audio_path, output_filename)
            output_path = "/home/aac/I+D/TEST/MUXICA/C1/3-Medidas/P1/leq_oct_test.csv"
            df.to_csv(output_path, index=False)
            logging.info(f"Output saved to {output_path}")
            print(f"Output saved to {output_path}")
        else:
            logging.warning(f"No data to save for folder {subfolder}")


if __name__ == "__main__":
    main()
