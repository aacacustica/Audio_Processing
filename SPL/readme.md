# Sound Pressure Levels

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
