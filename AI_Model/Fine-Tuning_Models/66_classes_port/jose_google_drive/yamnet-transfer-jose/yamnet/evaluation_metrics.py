import pandas as pd
import tensorflow as tf 
import os
import resampy
import soundfile as sf
import matplotlib.pyplot as plt
import numpy as np
from tqdm import tqdm
import datetime
import argparse
import h5py

# Model specific
import params as yamnet_params
import yamnet as yamnet_model

input_folder = ""
output_filename = ".h5"
dataset_file = "../audioset_eval_strong_filt_downloaded.csv"

#### Load Base model 

# The graph is designed for a sampling rate of 16 kHz, but higher rates should work too.
# We also generate scores at a 10 Hz frame rate.
sr = 16000
params = yamnet_params.Params(sample_rate=sr, patch_hop_seconds=1)
print("Sample rate =", params.sample_rate)

# Set up the YAMNet model.
class_names = yamnet_model.class_names('yamnet_class_map.csv')
yamnet = yamnet_model.yamnet_frames_model(params)
yamnet.load_weights('yamnet.h5')

df_class_map = pd.read_csv("yamnet_class_map.csv")

mid_dict = {mid:i for i, mid in enumerate(df_class_map["mid"].values)}
index_dict = {i:mid for i, mid in enumerate(df_class_map["mid"].values)}

def mid_to_index(mid):
    return mid_dict[mid]

def index_to_mid(mid):
    return index_dict[mid]

def load_audio(filename):
    x, _ = sf.read(filename)
    if len(x.shape) > 1:
        x = np.mean(x, axis=1)
    return x

##### Read Database

df_metadata = pd.read_csv(dataset_file)
df_metadata["label_yamnet"] = df_metadata.apply(lambda x: mid_to_index(x["label"]),  axis=1)


### get socres
all_scores = []
ground_truth = []

for i,clip in tqdm(df_metadata.iterrows()):
    x = load_audio(clip["path"])
    scores, embeddings, spectrogram = yamnet(x)
    scores = scores.numpy()
    mean_scores = np.mean(scores, axis=0)
    all_scores.append(mean_scores)
    ground_truth.append(clip["label_yamnet"])

### Save data

yamnet_predictions = h5py.File("yamnet_predictions_eval_audioset.h5",'w')
yamnet_predictions.create_dataset(name="y",dtype=np.int8,data=np.asarray(ground_truth))
yamnet_predictions.create_dataset(name="y_hat",dtype=np.float32,data=np.asarray(all_scores))