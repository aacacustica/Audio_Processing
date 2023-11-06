# AudioMoth Data Visualization Tool

This tool is designed to visualize sound level data collected using the AudioMoth device. It generates heatmaps and time plots for given sound level data, providing a visual representation of the sound levels over time.

## Features

- **Heatmap Generation:** Creates a heatmap based on daily and hourly aggregated sound levels.
- **Time Plot Generation:** Generates time plots with customizable percentiles, providing a temporal view of sound levels.
- **Percentile Plotting:** Users can choose specific percentiles to be plotted on the time plot.

## Requirements

To use this tool, you will need:

- Python 3.6 or higher.
- Pandas, Matplotlib, Seaborn, and NumPy libraries installed.

## Usage

Run the script from the command line, providing the necessary arguments:

```bash
python audiomoth_visualization.py -f <csv_file> [-a <agg_period>] [-o <output_dir>] [-p <percentiles...>]
```

## Arguments

    -f, --csv-file (required): Path to the CSV file containing AudioMoth data.
    -a, --agg_period (optional): Aggregation period in seconds for plotting. Default is 900 seconds.
    -o, --output-dir (optional): Directory where the output files will be saved. Defaults to the current directory.
    -p, --percentiles (optional): Space-separated list of percentiles to plot (e.g., -p 90 50). Defaults to L90 and L10.

## Output

The script will output:

    A heatmap as a PNG file showing the aggregated sound levels.
    A CSV file with the heatmap data.
    A time plot PNG file for the specified percentiles.

## Example

To generate visualizations with the default settings:

```bash
python audiomoth_visualization.py -f data.csv
```

To specify an aggregation period of 600 seconds and plot the L90 and L50 percentiles:

```bash
python audiomoth_visualization.py -f data.csv -a 600 -p 90 50
```

To save the output in a specific directory:

```bash
python audiomoth_visualization.py -f data.csv -o /path/to/output
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.