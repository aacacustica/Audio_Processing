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
python urban_model.py -p "\\192.168.205.117\AAC_Server\PUERTOS\NOISEPORT\20231211_SANTUR\3-Medidas\P1_CONTENEDORES\AUDIOMOTH" -w 15 -n 3 -r </path/to/results>
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

### Overview
This Python script is designed for visualizing audio classification results. It processes a CSV file containing audio classification data, generates a heatmap of classes over time, and saves the visualization as an image. The script also provides options for handling audio file intervals and class label manipulations.

### Prerequisites
Before running this script, ensure you have the following Python packages installed:

- `pandas`
- `seaborn`
- `matplotlib`
- `ast`
- `numpy`
- `os`
- `subprocess`

### Installation
Install the required Python packages using pip:

```bash
pip install pandas seaborn matplotlib numpy
```

### Usage
To use this script, you need to provide the path to a CSV file containing audio classification results. The script performs several operations including extracting the location from the file name, processing class labels, and generating a heatmap.

### Running the Script
Run the script in a Python environment.
Input the path to the CSV file when prompted.
The script will process the data and generate a heatmap visualization.

```bash
"\\192.168.205.117\AAC_Server\PUERTOS\NOISEPORT\20231211_SANTUR\5-Resultados\P1_CONTENEDORES\URBAN_Model\Predictions\Urban_Model_P1_CONTENEDORES_v1_0.csv"
```

### Key Functions
- `Location Extraction:` Extracts the location identifier from the file name.
- `Label Processing:` Includes functions to remove or change labels, and select the first element from class lists.
- `Interval Printing:` Prints the average interval between audio files based on predefined constants.
- `Date Insertion:` Enhances the DataFrame with additional date and time columns for detailed analysis.
- `Output Directory Creation:` Creates a directory for saving visualizations.
- `Heatmap Generation:` Generates a heatmap of classes over time and saves it as an image.

### Visualization
The output is a heatmap saved as an image in a visualization directory. The heatmap displays the distribution of audio classes across different times of the day.

### Customization
You can modify the script to handle different class labels or adjust the visualization parameters according to your dataset.

### Output
The script saves the generated heatmap image in a specified directory. The file name includes the location identifier and the stable version tag obtained from the Git repository.

### Note
The script uses Git tags to manage versions. Ensure your Git environment is properly set up if you're using this feature.