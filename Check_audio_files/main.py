from process_metadata import *

def main():
    file_path = "/home/santi/Documents/AAC/audios/20231019_173510.WAV"
    folder_path = "/home/santi/Documents/AAC/audios/"
    metadata = get_metadata(file_path)
    print(metadata)

if __name__ == "__main__":
    main()