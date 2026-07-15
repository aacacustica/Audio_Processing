import os

def get_audiofiles(path):
    """
    Args:
        path (str): The path to the directory containing the audio files.
    Returns:
        list: A list containing the full paths to all '.wav' files in the specified directory.
    """
    audio_files = [file for file in os.listdir(path) if file.lower().endswith('.wav')]
    return audio_files


def get_device_id(metadata):
        artist_tags = metadata.tags.get("artist", ["songmeter"])
        if not artist_tags or len(artist_tags[0].split(" ")) < 2:
            return "songmeter"
        
        return artist_tags[0].split(" ")[1].lower()