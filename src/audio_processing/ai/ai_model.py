import resampy

import numpy as np
import soundfile as sf

from pathlib import Path

import audio_processing.ai.yamnet as yamnet_model
import audio_processing.ai.params as yamnet_params
  
from audio_processing.campaign.config import load_config

from audio_processing.ai.utils_ai import save_spectrogram_w_funct

config = load_config()


class AudioClassifier:

    def __init__(self):

        self.params = yamnet_params.Params()
        self.yamnet = yamnet_model.yamnet_frames_model(self.params)

        self.yamnet.load_weights('src/audio_processing/ai/yamnet.h5')
        self.yamnet_classes = yamnet_model.class_names('src/audio_processing/common/yamnet_class_map.csv')

        ai_dir = (Path(__file__)).resolve().parent
        weights_path = (ai_dir / "yament.h5")
        class_map_path = (ai_dir.parent / "common" / "yamnet_class_map.csv")

    def predict_file(self,file_path: Path,window_seconds:float,*,logger=None) -> list[np.ndarray]:

        waveform,sample_rate = sf.read(file_path,dtype = "float32")
        target_sample_rate = int(self.params.sample_rate) 
        predictions = []

        if waveform.ndim > 1:

            waveform = np.mean(waveform,axis = 1)

            if logger: logger.warning(f"Audio multicanal {file_path} se usará en la media.")

        if sample_rate != target_sample_rate:

            if logger: logger.info(f"Resampling {file_path}: {sample_rate} -> {target_sample_rate}")

            waveform = resampy.resample(waveform,sample_rate,target_sample_rate)
            sample_rate = target_sample_rate

        window_samples = int(window_seconds * sample_rate)

        for start in range(0,len(waveform),window_samples):

            window = waveform[start:start + window_samples]

            if len(window) == 0: continue

            scores, _ , _ = self.yamnet(window)

            prediction = np.mean(scores.numpy(),axis = 0)

            predictions.append(prediction)

        return predictions

    def process_single_file(self, file_path,logging):

        logging.info(f"\n Processing file: {file_path}")

        wav_data,sr = sf.read(file_path,dtype=np.int16)
        waveform = wav_data / 32768.0
        waveform = waveform.astype('float32')

        if len(waveform.shape) > 1:
            waveform = np.mean(waveform,axis=1)
            logging.warning(f"Audio file has more than 1 channel. Taking the mean of all channels.")

        if sr != self.params.sample_rate:
            waveform = resampy.resample(waveform,sr,self.params.sample_rate)
            logging.warning(f"Resampling audio from {sr} to {self.params.sample_rate}")

        predictions = []
        all_embeddings = []

        if AI_WINDOW_SECONDS is None:

            logging.info(f"Processing whole file without window size.")
            logging.info(f"Waveform shape: {waveform.shape}")

            scores,embeddings,spectrogram = self.yamnet(waveform)

            if AI_SAVE_ESPECTROGRAMS:

                scores = scores.numpy()
                spectrogram = spectrogram.numpy()
                save_spectrogram_w_funct(spectrogram,scores,self.yamnet_classes,file_path,self.params.sample_rate)

            prediction = np.mean(scores, axis=0)
            predictions.append(prediction)

            if AI_SAVE_EMBEDDINGS: all_embeddings.append(embeddings.numpy())

            return predictions,all_embeddings
                

        else:

            logging.info(f"Processing file with window size: {AI_WINDOW_SECONDS}")
            logging.info(f"Waveform shape: {waveform.shape}")

            window_size_samples = int(AI_WINDOW_SECONDS * sr)

            for start_idx in range(0, len(waveform),window_size_samples):

                end_idx = start_idx + window_size_samples
                if end_idx > len(waveform): end_idx = len(waveform)

                window = waveform[start_idx:end_idx]
                scores,embeddings,spectrogram = self.yamnet(window)

                if AI_SAVE_ESPECTROGRAMS:

                    scores = scores.numpy()
                    spectrogram = spectrogram.numpy()

                prediction = np.mean(scores,axis = 0)
                predictions.append(prediction)

                if AI_SAVE_EMBEDDINGS: all_embeddings.append(embeddings.numpy)

            return predictions,all_embeddings
