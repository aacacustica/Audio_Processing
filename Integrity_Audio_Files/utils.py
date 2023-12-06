import os

def make_json_directory(logger):
    current_directory = os.path.abspath(os.getcwd())
    # logger.info(current_directory)

    # make a directory for the json files
    json_directory = os.path.join(current_directory, "json_dicts")
    os.makedirs(json_directory, exist_ok=True)
    # logger.info(json_directory)

    return json_directory

def location_name(path, logger):
    return path.split("/")[-2]