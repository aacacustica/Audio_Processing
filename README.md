# AAC Noise Modeling

![aac_cover](https://github.com/santiagocampojurado/AAC/assets/89314673/6313860e-af09-4f5d-b8fd-d29b48f9f0e6)

## Links
<a href="https://twitter.com/intent/tweet?text=Wow:&url=https%3A%2F%2Fgithub.com%2Fsee2sound%2Fsee2sound">
  <img src="https://img.shields.io/twitter/url?style=social&url=https%3A%2F%2Fgithub.com%2Fsee2sound%2Fsee2sound" alt="Twitter">
</a>
<a href="https://arxiv.org/abs/2406.06612"><img src='https://img.shields.io/badge/arXiv-See2Sound-red' alt='Paper PDF'></a>
<a href='https://see2sound.github.io'><img src='https://img.shields.io/badge/Project_Page-See2Sound-green' alt='Project Page'></a>
<a href='https://huggingface.co/spaces/rishitdagli/see-2-sound'><img src='https://img.shields.io/badge/%F0%9F%A4%97%20Hugging%20Face-Spaces-blue'></a>
<a href='https://huggingface.co/papers/2406.06612'><img src='https://img.shields.io/badge/%F0%9F%A4%97%20Hugging%20Face-Paper-yellow'></a>

</div>
</div>


# About AAC

[AAC Centro de Acústica Aplicada](https://www.aacacustica.com/index.php) is an engineering firm specializing in noise and light pollution. With a commitment to independence and delivering tailored solutions, AAC is adept at addressing complex situations and managing large-scale projects. Our expertise is built on a foundation of technical knowledge and a dedicated approach to each case, ensuring that we not only meet but exceed the specific needs of our clients.


## Table of Contents

- [Description](#description)
- [Modules](#modules)
  - [Installation](#nstallation)
  - [AI Model](#ai-model)
  - [SPL](#spl)
  - [Visualization](#Visualization)
  - [Workflow](#workflow)
- [Contributing](#contributing)
- [License](#license)

## Description

This repository contains tools and scripts for audio analysis, specifically focusing on sound visualization and level measurements. The project aims to extract and visualize various metrics from audio files, ensuring accurate representation and calibration.

## Modules

### Installation

To get started, clone the repository and install the required packages:

```sh
git clone https://github.com/santiagocampojurado/AAC
cd AAC
pip install -r requirements.txt
```

### AI Model

The AI Model directory includes machine learning models for audio analysis, featuring visualization tools and YAMNet, a deep learning model for sound event detection and classification. It has two different folders: Urban and Port. Each contains the necessary Python, CSV, and H5 files for inference and predictions on entire audio files. Note that for the Port model, classifications below a 30% threshold are filtered out and not considered.

#### Feature
- `Audio Classification:` Classifies audio files using YAMNet.
- `Embeddings:` Option to save embeddings for further analysis.
- `Spectrograms:` Option to save spectrogram images for visualization.
- `Windowed Processing:` Supports processing of audio files in windows for detailed analysis.

#### Usage
To run the script, use the following command:

```sh
python inference_aac.py -p "<path_to_audio_directory>" [options]
```

#### Options
- `-p, --path:` Directory to be processed (required).
- `-w, --window`: Window size in seconds for processing audio files. Default is None for processing full audio.
- `-t, --threshold`:` Classification threshold for predictions.
- `--embeddings:` Save embeddings to tensorboard.
- `--spectrogram:` Save spectrogram images.

#### Example
```sh
python inference_aac.py -p "\\192.168.205.117\AAC_Server\OCIO\OCIO_BILBAO\CAMPAÑA_5"
```

#### Script Details

#### Main Components

##### Imports
The script imports several necessary modules for audio processing, including os, numpy, tqdm, resampy, soundfile, logging, and custom utilities and parameters from utils, params, and yamnet.

##### Logging
Configured to log information, warnings, and errors to yamnet_inference.log.

##### Class: AudioClassifier
Handles the audio classification process using YAMNet.

#### Methods
`__init__:` Initializes the classifier, loads the YAMNet model and its parameters.
`process_single_file:` Processes a single audio file, optionally saving embeddings and spectrograms.

  - Reads the audio file.
  - Converts to mono and resamples if needed.
  - Processes the entire file or in windows.
  - Logs warnings for non-mono files and resampling actions.

##### Function: process_audio_files
Processes multiple audio files within a specified directory.

  - Searches for subfolders containing audio files.
  - Reads metadata for each audio file.
  - Processes each audio file using AudioClassifier.
  - Saves predictions and embeddings as needed.

##### Function: parse_arguments
Parses command-line arguments for running the script.

  - `-p, --path:` Directory to be processed.
  - `-w, --window:` Window size in seconds for processing.
  - `-t, --threshold:` Classification threshold.
  - `--embeddings:` Option to save embeddings.
  - `--spectrogram:` Option to save spectrograms.

##### Helper Functions

  - `setup_gpu:` Configures GPU settings for TensorFlow.
  - `get_stable_version:` Retrieves the stable version of the model or script.
  - `find_audiomoth_folders:` Finds subfolders containing audio files.
  - `get_audiofiles:` Retrieves a list of audio files in a specified directory.
  - `save_spectrogram_w_funct:` Saves spectrogram images.
  - `save_embeddings_funct:` Saves embeddings to specified location.
  - `save_predictions_to_csv:` Saves predictions to a CSV file.

##### Logging
Logs are saved in yamnet_inference.log to track processing steps, warnings, and errors.


### SPL

The SPL directory focuses on Sound Pressure Level (SPL) measurement analysis, including Leq levels and visualization tools.

- `Leq_level`: Script for calculating Leq levels.
- `Leq_level_oct`: Script for octave band Leq level calculation.
- `Leq_level_oct_FFT`: Script for Leq level calculation with FFT.

This script calculates Sound Pressure Level (SPL) measurements for audio files, including A-weighted, C-weighted, and unweighted levels. It supports processing audio files in a specified directory, reading metadata, and saving the calculated levels to a CSV file.

#### Features
`SPL Calculation:` Calculates A-weighted (LA), C-weighted (LC), and unweighted (LZ) sound levels.
`Windowed Analysis:` Supports analysis in specified time windows.
`Metadata Reading:` Extracts metadata from audio files for processing.
`CSV Output:` Saves the SPL measurements to a CSV file for further analysis.

#### Usage
To run the SPL analysis script, use the following command:

````sh
python leq_level.py -p "<path_to_audio_directory>"
````

#### Options
  - `-p, --path:` Directory to be processed (required).

#### Example
````sh
python leq_level.py -p "\\192.168.205.117\AAC_Server\PUERTOS\NOISEPORT\20231211_SANTUR\"
````

#### Script Details
##### Imports
The script imports necessary modules for SPL analysis, including `pandas`, `soundfile`, `scipy.signal`, `numpy`, `pyfilterbank.splweighting`, and custom utilities from `utils`.

##### Logging
Configured to log `information`, `warnings`, and `errors` to `leq_level.log`.

##### Class: LeqLevel
Handles the SPL calculation process.

##### Methods
- `__init__:` Initializes the SPL calculator with sample rate, calibration constant, and window size.
- `calculate_spl_levels:` Calculates SPL levels for given audio data.
- `A-weighted (LA)`, `C-weighted (LC)`, and `unweighted (LZ)` levels.
- `Maximum (Lmax)` and `minimum (Lmin)` levels within the window.
- `LC -LA` level.
- `Function:` read_calibration_constants
- Reads calibration constants from a specified `INI` file.

##### Function: get_device_id
Extracts the device ID from audio metadata.

##### Function: find_audiomoth_folders
Finds subfolders containing audio files in the specified base path.

##### Function: parse_arguments
Parses command-line arguments for running the script.

##### Helper Functions
- `get_audiofiles:` Retrieves a list of audio files in a specified directory.
- `get_db_level:` Calculates the decibel level for given audio data.
- `setup_gpu:` Configures GPU settings for TensorFlow (if needed).
- `get_stable_version:` Retrieves the stable version of the model or script.

##### Logging
Logs are saved in leq_level.log to track processing steps, warnings, and errors.

##### Workflow
- `Initialization:` Set up the SPL calculator with sample rate, calibration constant, and window size.
- `Metadata Reading:` Extract metadata from audio files to determine sample rate and device ID.
- `SPL Calculation:` Calculate SPL levels for each audio file.
- `CSV Output:` Save the calculated SPL levels to a CSV file.


### Visualization
This folder contains scripts and configurations for plotting and visualizing audio data collected from AudioMoth and sonometer devices. The main script, main.py, processes the audio data and generates various plots to aid in the analysis of sound levels and events.

#### Features
  - `Data Aggregation:` Supports aggregation of data over specified periods.
  - `Taxonomy Processing:` Processes data using urban or port taxonomies.
  - `Visualization:` Generates multiple types of plots to visualize audio data trends and predictions.

#### Usage
To run the visualization script, use the following command:

````sh
python main.py -f "<path_to_sonometers_folder>" [options]
````

#### Options
  - ` -f, --path_general:` Path to the folder containing AudioMoth or sonometer data (required).
  - `-a, --agg_period:` Aggregation period in seconds (default: 900 seconds).
  - `-o, --output-dir:` Output directory for the plots (default: same as input directory).
  - `-p, --percentiles:` Percentiles to plot (default: [90, 10]).
  - `--audiomoth:` Process AudioMoth data.
  - `--sonometer:` Process sonometer data.
  - `--urban:` Use urban taxonomy for classification.
  - `--port:` Use port taxonomy for classification.
  - `--change-date`: Change the date and the time of the csv file.


#### Example

````sh
python main.py -f "\\192.168.205.117\AAC_Server\OCIO\OCIO_BILBAO\FASE_3" --audiomoth --urban
````

#### Script Details

##### Imports
The script imports necessary modules for argument parsing, logging, configuration, and data processing.

##### Logging
Configured to log information, warnings, and errors to visualization.log.

##### Function: arg_parser
Parses command-line arguments for running the script.

##### Function: main
Main function to process audio data and generate plots.

  - `Argument Parsing:` Parses input arguments and sets default values.
  - `Taxonomy Loading:` Loads urban or port taxonomy based on input arguments.
  - `Folder Processing:` Identifies folders containing AudioMoth or sonometer data and processes them.
  - `Data Aggregation:` Aggregates data over specified periods and calculates percentiles.
  - `Plot Generation:` Generates various plots based on the processed data.

##### Helper Functions
  - `setup_logging:` Configures the logging settings.
  - `yamnet_class_map_csv:` Loads YAMNet class map CSV file.
  - `taxonomy_json:` Loads urban and port taxonomy JSON files.
  - `process_all_folders:` Processes all identified folders and generates plots.

#### Plots Generated
The script can generate the following plots:

##### Night Evolution Plots:

  - `PLOT_NIGHT_EVOLUTION`
  - `PLOT_NIGHT_EVOLUTION_15_MIN`

##### LAeq Prediction Plots:

  - `PLOT_PREDIC_LAEQ_15_MIN`
  - `PLOT_PREDIC_LAEQ_15_MIN_PERIOD`
  - `PLOT_PREDIC_LAEQ_15_MIN_4H`

##### Prediction Visualizations:

  - `PLOT_PREDICTION_STACK_BAR`
  - `PLOT_PREDICTION_MAP`
  - `PLOT_TREE_MAP`

##### Time Plots:

  - `PLOT_MAKE_TIME_PLOT`

##### Heatmap Plots:

  - `PLOT_HEATMAP_EVOLUTION_HOUR`
  - `PLOT_HEATMAP_EVOLUTION_15_MIN`
  - `PLOT_INDICADORES_HEATMAP`

##### Evolution Plots:

  - `PLOT_DAY_EVOLUTION`
  - `PLOT_PERIOD_EVOLUTION`
  - `These plots visualize the evolution of audio levels and predictions over different time periods and conditions.

### Workflow

The Workflow directory includes diagrams and images that outline the audio analysis process and server setup.

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change. Ensure to update tests as appropriate.

## License

All content is licensed under the terms of The Unlicense. For more information, please refer to [The Unlicense](https://unlicense.org).
