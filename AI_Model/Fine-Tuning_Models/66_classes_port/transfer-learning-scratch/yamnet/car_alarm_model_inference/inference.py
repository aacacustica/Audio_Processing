import tensorflow as tf
import tensorflow_io as tfio

class ReduceMeanLayer(tf.keras.layers.Layer):
    def __init__(self, axis=0, **kwargs):
        super().__init__(**kwargs)
        self.axis = axis

    def call(self, inputs):
        return tf.math.reduce_mean(inputs, axis=self.axis)

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

model_path = r'C:\Users\GIS2\Documents\santi\GitHub\AAC\AI_Model\Fine-Tuning_Models\66_classes_port\transfer-learning-scratch\yamnet\cars_and_alarms_yamnet.h5'
model = tf.keras.models.load_model(model_path, custom_objects={'ReduceMeanLayer': ReduceMeanLayer})

testing_wav_file_name = r"C:\Users\GIS2\Documents\santi\GitHub\AAC\AI_Model\Fine-Tuning_Models\66_classes_port\transfer-learning-scratch\yamnet\-0x1a0a4fce078dd9e.wav"

testing_wav_data = load_wav_16k_mono(testing_wav_file_name)

predictions = model.predict(testing_wav_data)
print(predictions)