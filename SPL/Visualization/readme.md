# Sound Pressure Levels

<br>

## Table of Contents

- [Dash](#Dash)
- [Sonometer-AudioMoth](#Sonometer-AudioMoth)
- [Spectrogram](#Spectrogram)

<br>
<br>

## [Dash](#Dash)

This script is designed to process audio files and extract various metrics, specifically LA, LC, LZ, LAmax, and LAmin levels.

### Features

- Extracts the metrics LA, LC, LZ, LAmax, and LAmin levels from audio files.
- Logs all operations to a file named `leq_levels.log`.
- Processes all `.wav` files in a specified directory.
- Determines the predominant sample rate across files.
- Uses calibration constants from a file, with a default of `calibration_constants.ini`.
- Saves metrics to CSV files, which can be sorted by date.

### Usage
```bash
python <script_name>.py -p <path_to_audio_files> [-c <calibration_constants_file>] [-r <result_directory>]
```
### Arguments

    -p, --path: Directory path containing the audio files to process. This is a required argument.
    -c, --calibration: Calibration constants file path. By default, this is set to calibration_constants.ini.
    -r, --result-dir: Directory where the resulting CSV files should be saved. If not specified, it saves in the default directory.

### Important Notes

The program logs information, warnings, and errors to a file named `leq_levels.log`.
The default calibration constant, in the absence of a specific device calibration, is `-10.16`.
The program expects audio files to be in `.wav` format.

<br>
<br>

## [Sonometer-AudioMoth](#Sonometer-AudioMoth)


This script is designed to process the visualization of csv files. 
It allows users to specify parameters such as the path to the sonometers folder, aggregation period, percentiles for plotting, and an output directory.

## Prerequisites
Before running this script, ensure that you have Python installed on your system. Additionally, you should have the following Python packages installed:

- `argparse`
- `os`
- `logging_config` (custom module)
- `config` (custom module)
- `sound_data_processing` (custom module)

## Installation
Install the required Python packages using pip, if they are not already installed:

```bash
pip install argparse os
```
# Install any other dependencies that are specific to your project
## Usage
To use this script, run it from the command line with the required and optional arguments.

## Required Arguments

- `-f, --path_sonometers:` Path to the sonometers folder.


## Optional Arguments
- `-a, --agg_period:` Aggregation period in seconds. Default is 900 seconds (15 minutes).
- `-o, --output-dir:` Output directory. If not provided, the output directory is the same as the input directory.
- `-p, --percentiles:` Percentiles to plot (e.g., [90, 10]). Default is L90 and L10.

## Example Command
```bash
python main.py -f "C:/Users/usuario/Desktop/sonometers" -a 900 -p 90 10
```
## Output
The script creates a folder with the same name as the sonometer folder in the output directory. Inside this folder, it creates a folder for each sonometer with the corresponding plots.

## Help Command
For a detailed description of all the available options and default values, run the help command:

```bash
python main.py -h
```

## Logging
The script uses a custom logging configuration. Ensure that the `logging_config` module is correctly set up to capture logs as desired.

<br>
<br>

### [Spectrogram](#Spectrogram)

This Python script is designed for plotting spectrograms from audio files or CSV data. It supports various audio formats and can plot octave band data from CSV files. The script generates visual representations of spectral data over time, useful for analyzing audio characteristics.

## Prerequisites

Libraries: pandas, numpy, matplotlib, librosa, argparse, os
Audio files in .wav, .mp3, .flac formats or CSV files containing octave band data.
Installation
Ensure you have Python 3.x installed along with the required libraries. You can install the libraries using pip:

```bash
pip install pandas numpy matplotlib librosa
```

## Usage
The script can be used in two modes: Audio and CSV.

## For Audio Files
To plot spectrograms from audio files, use the following command:

```bash
python plot_spectrogram_octave.py -p "path_to_audio_file" -t audio [-sd start_db] [-ed end_db]
```
- p: Path to the audio file or directory containing audio files.
- t audio: Indicates the script to process audio files.
- sd: (Optional) Start decibel for the spectrogram.
- ed: (Optional) End decibel for the spectrogram.

## For CSV Files
To plot octave band spectrograms from CSV data, use this command:

``` bash
python plot_spectrogram_octave.py -p "path_to_csv_file" -i interval [-s start_time] [-e end_time]
```

    -p: Path to the CSV file.
    -i: Interval in minutes for x-axis ticks in the plot.
    -s: (Optional) Start time for filtering the data.
    -e: (Optional) End time for filtering the data.


## Parameters

- `start_db` and `end_db` are used for setting the dB range in audio spectrograms.
- `start_time` and `end_time` are used to filter the data by time in CSV spectrograms.
- `interval` sets the x-axis tick interval for CSV spectrograms.

## Output
The script generates spectrogram images and saves them in a Spectrogram folder within the same directory as the input files. For CSV files, it also generates an Excel file with the processed data.
