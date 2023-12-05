from pydub.utils import mediainfo
import os
import tqdm
# import argparse

def get_metadata(path: str):
    """Returns a dictionary with the metadata of the file or files in the path.
    Args: 
        path (str): Path to the file or folder.
    Returns:
        metadata_dict (dict): Dictionary with the metadata of the file or files.
    """

    # if path exists
    if not os.path.exists(path):
        raise Exception("Path does not exist.")
    
    # if path is a file or a folder
    if os.path.isdir(path):
        metadata_dict = {}
    
        # for files in folder
        for file in tqdm.tqdm(os.listdir(path)):
            full_path = os.path.join(path, file)
            if os.path.isfile(full_path):
    
                try:
                    # metadata
                    metadata = mediainfo(full_path)
                    metadata_dict[file] = metadata
                
                except Exception as e:
                    print(f"Error processing {file}: {e}")
    
        return metadata_dict
    
    else:
        try:
            # metadata
            metadata = mediainfo(path)
            return metadata
        
        except Exception as e:
            raise Exception(f"Error processing file: {e}")


















# def argument_parser():
#     """Argument parser to set the parameters of the script to 
#     check the integrity of audio files."""

#     parser = argparse.ArgumentParser(description="Process metadata of audio files.")
#     parser.add_argument("-p", "--path", type=str, help="Path to the file or folder.", required=False)
#     parser.add_argument("-o", "--output", type=str, help="Path to the output file.", required=False)

#     parser.add_argument("-sr", "--samplerate", type=int, help="Sample rate of the audio files.", required=False, default=16000)
#     parser.add_argument("-c", "--channels", type=int, help="Number of channels of the audio files.", required=False, default=1)
#     parser.add_argument("-g", "--gain", type=int, help="Gain of the audio files.", required=False, choices=["Low", "Med", "High"], default="Med")
#     parser.add_argument("-sd", "--sleep-duration", type=int, help="Sleep duration of the audio files in seconds.", required=False, default=5)
#     parser.add_argument("-d", "--duration", type=int, help="Duration of the audio files in seconds.", required=False, default=55)


#     return parser.parse_args()