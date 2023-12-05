from process_metadata import *
from logging_config import setup_logging

def main():
    logger = setup_logging()

    path = "/home/santi/Documents/AAC/audios/20231019_173510.WAV"
    # path = "/home/santi/Documents/AAC/audios/"
    # path = input("Enter path for the file or folder: ")
    
    try: 
        metadata = get_metadata(path, logger)
        # for key, value in metadata.items():
        #     logger.debug(f"{key}: {value}")

    except Exception as e:
        logger.error("Error: ", e)


if __name__ == "__main__":
    main()