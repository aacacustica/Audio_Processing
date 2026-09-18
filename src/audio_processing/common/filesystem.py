import os
import audio_metadata
import tqdm

from pathlib import Path

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


def get_metadata_audio(audio_files: list,audio_path: str | Path,logging):

    sample_rates = []
    valid_audio_files = []

    for file in tqdm.tqdm(audio_files, desc='Reading metadata'):

        try:

            metadata = audio_metadata.load(os.path.join(audio_path,file))
            sample_rates.append(metadata.streaminfo.sample_rate)
            valid_audio_files.append(file)
        except Exception as e:
                logging.warning(f"Error reading file metadata: {file}, {e}")
                continue

    if (not sample_rates) or (not valid_audio_files):
        logging.warning(f"No valid audio files to process in {audio_path}. Skipping.")
        return

    return valid_audio_files
     

