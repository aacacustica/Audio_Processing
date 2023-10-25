# Sound Pressure Levels

## Table of Contents

- [Leq Level](#leq-level)
- [1/3 Octave](#13-octave)
- [1/3 Octave FFT](#13-octave-fft)


## [Leq Level](#leq-level)

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

The program logs information, warnings, and errors to a file named leq_levels.log.
The default calibration constant, in the absence of a specific device calibration, is -10.16.
The program expects audio files to be in .wav format.


## [1/3 Octave](#13-octave)


This script is designed to process audio files and analyze their 1/3 octave bands.

### Features

- Analyzes the 1/3 octave bands from audio files.
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

The program logs information, warnings, and errors to a file octave_analysis.log.
The default calibration constant, in the absence of a specific device calibration, is -10.16.
The program expects audio files to be in .wav format.


## [1/3 Octave FFT](#13-octave-fft)

This script is designed to process audio files and analyze their 1/3 octave bands using Fast Fourier Transform (FFT).

### Features

- Analyzes the 1/3 octave bands from audio files using FFT.
- Logs all operations to a file named `octave_fft_analysis.log`.
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

The program logs information, warnings, and errors to a file octave_fft_analysis.log.
The default calibration constant, in the absence of a specific device calibration, is -10.16.
The program expects audio files to be in .wav format.
