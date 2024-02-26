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

print("running TF version",tf.__version__)

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

##### Create embedding Model 

embedding_layer = tf.keras.Model(inputs=yamnet.input,
                                 outputs=yamnet.get_layer('global_average_pooling2d').output)
embedding_layer.trainable = False

##### Read Database

df_metadata = pd.read_csv(dataset_file)

df_metadata["label"] = df_metadata["label"].astype("category")
category_map = pd.DataFrame( df_metadata["label"].cat.categories )
category_map.to_csv("category_map.csv")

df_metadata["label_id"] = df_metadata["label"].cat.codes
df_metadata["path"] = df_metadata["path"].str.replace("audioSet_eval","eval_16k")

filenames = df_metadata["path"].values
targets = df_metadata["label_id"].values
labels = df_metadata["label"].values
n_classes = 66
embedding_size = 1024

print(labels)

def load_audio(filename):
    x, _ = sf.read(filename)
    if len(x.shape) > 1:
        x = np.mean(x, axis=1)
    return x

##### Processing loop

all_embeddings = np.empty([1,embedding_size])
all_labels = np.zeros(1)
embedding_counter = 0
file_counter=1

for file, label in (zip(tqdm(filenames), targets)):
    
    x = load_audio(file)
    embeddings = embedding_layer(x)
    all_embeddings = np.concatenate( [all_embeddings, embeddings] )
    embedding_counter += embeddings.shape[0]
    all_labels = np.concatenate( [all_labels,np.repeat(label,embeddings.shape[0])] )

    if embedding_counter > (10000):
        # Save h5py file
        filename = f"embeddings_eval_{file_counter}.h5"
        with h5py.File(filename, "w") as f:
            embeddings_dataset = f.create_dataset("embeddings", data=all_embeddings)
            labels_dataset = f.create_dataset('labels', data=all_labels)

        # Reset arrays
        all_embeddings = np.empty([1,embedding_size])
        all_labels = np.zeros(1)
        embedding_counter = 0
        file_counter+=1

print("::: Features extracted :::")