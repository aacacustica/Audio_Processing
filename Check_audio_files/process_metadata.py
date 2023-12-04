from pydub.utils import mediainfo
import json

def get_metadata(file_path: str):
    """Get metadata from audio file
    Args:
        file_path (str): path to audio file
    Returns:
        metadata_json (json): metadata from audio file"""
    
    metadata = mediainfo(file_path)
    metadata_json = json.dumps(metadata, indent=4)
    return metadata_json