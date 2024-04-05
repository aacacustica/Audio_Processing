import tensorflow as tf

def setup_gpu():
    physical_devices = tf.config.list_physical_devices('GPU')
    print("\nNum GPUs Available: ", len(physical_devices))
    for device in physical_devices:
        print(device)
        print()
    if physical_devices:
        try:
            tf.config.experimental.set_memory_growth(physical_devices[0], True)
        except RuntimeError as e:
            print(e)
            print()