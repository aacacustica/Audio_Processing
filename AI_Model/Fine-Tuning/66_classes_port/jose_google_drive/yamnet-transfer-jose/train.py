import numpy as np
import soundfile as sf
import librosa
import os
import tensorflow as tf
import pandas as pd

print("running TF version",tf.__version__)
## Read DATASET

METADATA_FOLDER = "/Users/wetdog/Documents/07_databases/ESC-50-master/meta/esc50.csv"
AUDIO_FOLDER = "/Users/wetdog/Documents/07_databases/ESC-50-master/audio"
df = pd.read_csv(METADATA_FOLDER)
df["filepath"] = df.apply(lambda x: os.path.join(AUDIO_FOLDER,x["filename"]), axis=1)
df.head()

