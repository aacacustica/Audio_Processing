import tensorflow as tf 
import h5py
import os
import datetime


data_dir = "/Users/wetdog/Documents/01_personal/research/yamnet-transfer/embeddings_data"
embedding_size = 1024

files = [os.path.join(data_dir,file) for file in os.listdir(data_dir)]
print(files)

hdf5_file = h5py.File(files[0],'r')
embeddings = hdf5_file["embeddings"][...]
labels = hdf5_file["labels"][...]
n_classes = 66

############## Model #######################


inputs = tf.keras.layers.Input(shape=(embedding_size), dtype=tf.float32,
                          name='input_embedding')
dense = tf.keras.layers.Dense(128, name='Hidden', activation="relu")(inputs)
outputs =  tf.keras.layers.Dense(n_classes, name="output",activation="softmax")(dense)


model = tf.keras.Model(inputs=inputs, outputs=outputs)

opt = tf.keras.optimizers.Adam(learning_rate=0.0001)
tensorboard_callback = tf.keras.callbacks.TensorBoard(log_dir="./logs")
model.compile(optimizer=opt,
              loss='categorical_crossentropy',
             metrics=["accuracy"],)
model.summary()


###### Data
x_tf = tf.constant(embeddings, dtype=tf.float32)

y_tf = tf.keras.utils.to_categorical(labels, num_classes = n_classes)

##### Training

start_date = datetime.datetime.strftime( datetime.datetime.now(), format="%Y%m%d_%H:%M:%S")
tensorboard_callback = tf.keras.callbacks.TensorBoard(log_dir=f"./logs/{start_date}")
model.fit(x=x_tf,
         y=y_tf,
         epochs=50,
          callbacks=[tensorboard_callback],
         batch_size=16)