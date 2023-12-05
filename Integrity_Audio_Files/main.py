from process_metadata import *
from test_integrity import *

def main():
    path = "/home/santi/Documents/AAC/audios/20231019_173510.WAV"
    # path = "/home/santi/Documents/AAC/audios/"
    
    # path = input("Enter path for the file or folder: ")
    
    try: 
        metadata = get_metadata(path)
        for key, value in metadata.items():
            print(f"{key}: {value}")
        # print(metadata)

        # testing integrity
        # calibration
        test_name_calibration(metadata)

        # test channels
        test_channels(metadata)

        # test sample rate
        test_sample_rate(metadata)
    
    except Exception as e:
        print("Error: ", e)


if __name__ == "__main__":
    main()