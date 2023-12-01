import mutagen

def read_audio_metadata(file_path):
    """
    Reads metadata from an audio file using mutagen.

    Args:
    file_path (str): Path to the audio file.

    Returns:
    dict: Metadata of the audio file.
    """
    try:
        audio_file = mutagen.File(file_path)
        if audio_file is None:
            return "Unsupported file format or file not found."

        metadata = {}
        if hasattr(audio_file, 'tags') and audio_file.tags is not None:
            for key, value in audio_file.tags.items():
                metadata[key] = value
        else:
            metadata = "No metadata found in file."

        return metadata
    except Exception as e:
        return str(e)

def main():
    file_path = "/home/santi/Documents/AAC/audios/0x1a0f3fd99b9cb830.wav"
    metadata = read_audio_metadata(file_path)
    print(metadata)

if __name__ == "__main__":
    main()
