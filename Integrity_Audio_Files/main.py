from process_metadata import *
from logging_config import setup_logging
import json

def main():
    logger = setup_logging()

    # path = "/home/santi/Documents/AAC/audios/20231019_173510.WAV"
    path = "/home/santi/Documents/AAC/audios/AudioMoths"
    
    try:
        metadata = get_metadata(path, logger)
        print(metadata)
        # save to json file
        with open("metadata_audiomoths.json", "w") as f:
            json.dump(metadata, f, indent=4)
            logger.info("Metadata saved in metadata.json")

    except Exception as e:
        logger.error("Error: %s", e)

if __name__ == "__main__":
    main()
