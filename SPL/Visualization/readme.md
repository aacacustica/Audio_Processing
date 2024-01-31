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


This script is designed to process audio files and analyze their Sonometer-AudioMoth bands.

### Features

- Analyzes the Sonometer-AudioMoth bands from audio files.
- Logs all operations to a file named `octave_analysis.log`.
- Processes all `.wav` files in a specified directory.
- Determines the predominant sample rate across files.
- Uses calibration constants from a file, with a default of `calibration_constants.ini`.
- Saves analyzed bands to CSV files, which can be sorted by date.

### Usage
```bash
python <script_name>.py -p <path_to_audio_files> [-c <calibration_constants_file>] [-r <result_directory>]
```
### Arguments

    -p, --path: Directory path containing the audio files to process. This is a required argument.
    -c, --calibration: Calibration constants file path. By default, this is set to calibration_constants.ini.
    -r, --result-dir: Directory where the resulting CSV files should be saved. If not specified, it saves in the default directory.

### Important Notes

The program logs information, warnings, and errors to a file `octave_analysis.log`.
The default calibration constant, in the absence of a specific device calibration, is `-10.16`.
The program expects audio files to be in `.wav` format.

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
