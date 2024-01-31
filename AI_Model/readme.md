# Urban Sound Classification with YAMNet

<br>

## Table of Contents

- [Fine-tuning-models](#Fine-tuning-models)
- [Urban-model](#Urban-model)
- [Visualization](#Visualization)

<br>
<br>

## [Fine-tuning-models](#Fine-tuning-models)

## [Urban-model](#Urban-model)

### Overview
This Python script is designed for analyzing urban sound recordings using the YAMNet model. It processes audio files to predict sound classes and maps these predictions to custom categories. The script handles various audio analysis tasks, including duration analysis, sample rate consistency checks, and generating predictions based on a customized taxonomy.


### Prerequisites
- Python with necessary libraries: `numpy`, `soundfile`, `scipy`, `os`, `tqdm`, `datetime`, `pandas`, `argparse`, `tensorflow`
- YAMNet model files and a custom class mapping file (`urban_taxonomy_map_v1_0.json`)
- Audio files in `.WAV` or `.wav` format

### Installation
Install the required dependencies using pip. TensorFlow installation might vary based on your system's specifications:

```bash
pip install numpy soundfile scipy pandas argparse tqdm
pip install tensorflow
```
### Usage
To use this script, run it from the command line with the required and optional arguments.

#### Required Arguments
- `-p, --path:` Path to the directory containing audio files.

#### Optional Arguments
- `-a, --abrev:` Abbreviation or identifier for the prediction files.
- `-w, --window:` Analysis window size in minutes. Default is 14.99 minutes.
- `-n, --n-predictions:` Number of predictions to generate. Default is 3.
- `-r, --result-folder:` Directory where results will be saved. If not specified, a default directory structure will be created.

### Example Command
```bash
python urban_model.py -p /path/to/audios -a "session1" -w 15 -n 3 -r /path/to/results
```

### Output
The script processes the audio files and generates a CSV file with the predictions, which includes details like file names, datetime of analysis, classes, and probabilities. This CSV file will be saved in the specified results folder or in the default directory structure.

### Logging
The script logs its process and errors to urban_model.log. Ensure the logging configuration is set up as needed.

### Custom Taxonomy Mapping
The script uses a custom taxonomy mapping (`urban_taxonomy_map_v1_0.json`). Ensure this file is present and correctly formatted for the script to function properly.

### GPU Configuration
The script is configured to utilize GPU for TensorFlow if available. Ensure your system has a compatible GPU and TensorFlow GPU version installed.

## [Visualization](#Visualization)