import tqdm
import os
import datetime

import numpy as np
import soundfile as sf
from pathlib import Path
from zoneinfo import ZoneInfo

from audio_processing.ai.utils_ai import find_audiomoth_folders,save_embeddings_funct,assign_prediction_class
from audio_processing.ai.writers import save_predictions_to_csv
from audio_processing.campaign.config import load_config
from audio_processing.common.filesystem import get_audiofiles,get_metadata_audio
from audio_processing.spl.utils_acoustics import timestamp_from_filename

from audio_processing.ai.ai_model import AudioClassifier
from audio_processing.ai.models import PredictionResult


def run_ai_for_file(audio_file: Path,*,classifier: AudioClassifier,config,logger=None) -> list[PredictionResult]:

    audio_file          = Path(audio_file)
    results             : list[PredictionResult] = []
    start_timestamp     = timestamp_from_filename(audio_file)
    info                = sf.info(audio_file)
    file_duration       = info.frames / info.samplerate
    window_seconds      = float(config.ai.window_seconds)
    threshold           = float(config.ai.threshold)
    top_k               = int(getattr(config.ai,"top_k",3))
    predictions         = classifier.predict_file(audio_file,window_seconds=window_seconds,logger=logger)
    

    if start_timestamp.tzinfo is None: start_timestamp = start_timestamp.replace(tzinfo=ZoneInfo(config.campaign.timezone))
        

    
    for window_index,prediction in enumerate(predictions):

        offset_seconds = window_index * window_seconds
        actual_window_seconds = min(window_seconds,file_duration - offset_seconds)

        if actual_window_seconds <= 0: continue

        timestamp = start_timestamp + datetime.timedelta(seconds = offset_seconds)
        top_indices = np.argsort(prediction)[::-1][:top_k]

        for rank,class_index in enumerate(top_indices,start=1):

            probability = float(prediction[class_index])

            if probability < threshold: continue

            results.append(
                PredictionResult(
                    timestamp       = timestamp,
                    window_seconds  = actual_window_seconds,
                    class_name      = str(classifier.yamnet_classes[class_index]),
                    probability     = probability,
                    rank            = rank
                )
            )

    return results



    

        



