import numpy as np
import soundfile as sf



class AudioClassifier:
    def __init__(self):
        self.params = yamnet_params.Params()
        self.yamnet = yamnet_model.yamnet_frames_model(self.params)
        self.yamnet.load_weights('yamnet.h5')
        self.yamnet_classes = yamnet_model.class_names('yamnet_class_map.csv')


    def process_single_file(self, file_path, window_size=None, save_embeddings=False, save_spectrogram=False):
        logging.info(f"\nProcessing file: {file_path}")
        
        wav_data, sr = sf.read(file_path, dtype=np.int16)
        waveform = wav_data / 32768.0  # Convert to [-1.0, +1.0]
        waveform = waveform.astype('float32')

        # convert to mono and resemple if needed (different from 16kHz)
        if len(waveform.shape) > 1:
            waveform = np.mean(waveform, axis=1)
            logging.warning(f"Audio file has more than 1 channel. Taking the mean of all channels.")
        if sr != self.params.sample_rate:
            waveform = resampy.resample(waveform, sr, self.params.sample_rate)
            logging.warning(f"Resampling audio from {sr} to {self.params.sample_rate}")


        # process audio file
        predictions = []
        all_embeddings = []
        if window_size is None:
            logging.info("Processing whole file without window size")
            logging.info(f"Waveform shape: {waveform.shape}")
            scores, embeddings, spectrogram = self.yamnet(waveform)

            if save_spectrogram:
                scores = scores.numpy()
                spectrogram = spectrogram.numpy()
                save_spectrogram_w_funct(spectrogram, scores, self.yamnet_classes, file_path, self.params.sample_rate)

            prediction = np.mean(scores, axis=0)
            predictions.append(prediction)

            if save_embeddings:
                all_embeddings.append(embeddings.numpy())
            return predictions, all_embeddings


        # process audio file with window size
        else:
            logging.info(f"Processing file with window size: {window_size}")
            logging.info(f"Waveform shape: {waveform.shape}")
            # if save_spectrogram:
            #     logging.info("Entering the window size analysis. But we run the whole audio file to save the complteted spectrogram.")
            #     scores, embeddings, spectrogram = self.yamnet(waveform)
            #     scores = scores.numpy()
            #     spectrogram = spectrogram.numpy()
            #     save_spectrogram_w_funct(spectrogram, scores, self.yamnet_classes, file_path, self.params.sample_rate)

            logging.info(f"Processing file with window size: {window_size}")
            window_size_samples = int(window_size * sr)

            for start_idx in range(0, len(waveform), window_size_samples):
                end_idx = start_idx + window_size_samples
                if end_idx > len(waveform):
                    end_idx = len(waveform)  # include the last segment
            
                window = waveform[start_idx:end_idx]
                scores, embeddings, spectrogram = self.yamnet(window)
                
                if save_spectrogram:
                    scores = scores.numpy()
                    spectrogram = spectrogram.numpy()
                    # save_spectrogram_w_funct(spectrogram, scores, self.yamnet_classes, file_path, self.params.sample_rate, start_idx, end_idx, window_size)

                prediction = np.mean(scores, axis=0)
                predictions.append(prediction)

                if save_embeddings:
                    all_embeddings.append(embeddings.numpy())
            return predictions, all_embeddings