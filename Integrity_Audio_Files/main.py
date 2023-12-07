from process_metadata import *
from utils import *
from test_metadata_integrity import *
from logging_config import setup_logging
import json

def main():
    logger = setup_logging()
    json_dir = make_json_directory(logger)

    # file
    # path = "/home/santi/Documents/AAC/audios/AudioMoths/20231019_220640.WAV"
    # folder
    path = "/home/santi/Documents/AAC/audios/AudioMoths"

    location = location_name(path, logger)

    try:
        # GETTING METADATA
        logger.info("Starting process...")
        metadata = get_metadata(path, logger)
        # logger.info(metadata)

        # save to json file
        with open(os.path.join(json_dir, f"metadata_{location}.json"), "w") as f:
            json.dump(metadata, f, indent=4)
            logger.info("Metadata saved in metadata.json")
        logger.info("Getting metadata finished")
        

        # TESTING METADATA
        logger.info("Starting testing...")

        # [1] open json file
        with open(os.path.join(json_dir, f"metadata_{location}.json"), "r") as f:
            metadata = json.load(f)
        # logger.info(metadata)

        # [2] test integrity
        test_integrity(metadata, logger)
    
    except Exception as e:
        logger.error("Error: %s", e)


if __name__ == "__main__":
    main()
