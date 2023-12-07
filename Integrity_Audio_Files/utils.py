import os


def make_json_txt_directory(path: str, logger):
    # current directory less the last folder
    current_directory = os.path.abspath(path).split("/")[:-1]
    current_directory = "/".join(current_directory)

    logger.info(f"make current dir at: {current_directory}")
    
    # make a directory for the json files
    audiomoth_metadata_dir = os.path.join(current_directory, "AUDIOMOTH_METADATA_TEST")
    os.makedirs(audiomoth_metadata_dir, exist_ok=True)
    logger.info(f"make audiomoth_metadata_dir at: {audiomoth_metadata_dir}")

    # make a directory for the json files
    json_directory = os.path.join(audiomoth_metadata_dir, "json_metadata")
    os.makedirs(json_directory, exist_ok=True)
    logger.info(f"make json_directory at: {json_directory}")

    # make a directory for the txt files
    txt_directory = os.path.join(audiomoth_metadata_dir, "txt_test")
    os.makedirs(txt_directory, exist_ok=True)
    logger.info(f"make txt_directory at: {txt_directory}")

    return json_directory, txt_directory



def location_name(path: str, logger):
    logger.info(f"location name: {path.split('/')[-2]}")
    return path.split("/")[-2]


