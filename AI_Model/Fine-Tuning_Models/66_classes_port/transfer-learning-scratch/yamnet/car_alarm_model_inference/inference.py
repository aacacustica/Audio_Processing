import tensorflow as tf
import tensorflow_io as tfio

def load_and_preprocess_audio(file_path, target_sample_rate=16000):
    audio = tfio.audio.AudioIOTensor(file_path)
    waveform = tf.squeeze(audio.to_tensor(), axis=-1)
    sample_rate = audio.rate

    if sample_rate != target_sample_rate:
        waveform = tfio.audio.resample(waveform, rate_in=sample_rate, rate_out=target_sample_rate)

    return waveform

@tf.function
def load_wav_16k_mono(filename):
    """ Load a WAV file, convert it to a float tensor, resample to 16 kHz single-channel audio. """
    file_contents = tf.io.read_file(filename)
    wav, sample_rate = tf.audio.decode_wav(
          file_contents,
          desired_channels=1)
    wav = tf.squeeze(wav, axis=-1)
    sample_rate = tf.cast(sample_rate, dtype=tf.int64)
    wav = tfio.audio.resample(wav, rate_in=sample_rate, rate_out=16000)
    return wav

loaded_model = tf.keras.models.load_model(r"C:\Users\GIS2\Documents\santi\GitHub\AAC\AI_Model\Fine-Tuning_Models\66_classes_port\transfer-learning-scratch\yamnet\cars_and_alarms_yamnet")

testing_wav_data = r"C:\Users\GIS2\Documents\santi\GitHub\AAC\AI_Model\Fine-Tuning_Models\66_classes_port\transfer-learning-scratch\yamnet\-0x1a0a4fce078dd9e.wav"

waveform = load_wav_16k_mono(testing_wav_data)

# Convert to mono and the sample's rate expected by YAMNet.
waveform = tf.squeeze(waveform, axis=-1)
waveform = tf.cast(waveform, tf.float32)

# Run the model.
scores, embeddings, spectrogram = loaded_model(waveform)
scores = tf.reduce_mean(scores, axis=0)
top_class = tf.argmax(scores)
infered_class = class_names[top_class]
print(f'The main sound is: {infered_class}')