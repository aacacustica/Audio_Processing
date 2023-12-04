from pydub.utils import mediainfo
import os
import tqdm

def get_metadata(path: str):
    if os.path.isdir(path):
        metadata_dict = {}
    
        # for file in os.listdir(path):
        for file in tqdm.tqdm(os.listdir(path)):
            full_path = os.path.join(path, file)
            if os.path.isfile(full_path):
    
                try:
                    metadata = mediainfo(full_path)
                    metadata_dict[file] = metadata
                except Exception as e:
                    print(f"Error processing {file}: {e}")
    
        return metadata_dict
    
    else:
        try:
            metadata = mediainfo(path)
            return metadata
        except Exception as e:
            raise Exception(f"Error processing file: {e}")
