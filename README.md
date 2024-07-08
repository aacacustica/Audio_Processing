# AAC Noise Modeling

![aac_cover](https://github.com/santiagocampojurado/AAC/assets/89314673/6313860e-af09-4f5d-b8fd-d29b48f9f0e6)

# About AAC

[AAC Centro de Acústica Aplicada](https://www.aacacustica.com/index.php) is an engineering firm specializing in noise and light pollution. With a commitment to independence and delivering tailored solutions, AAC is adept at addressing complex situations and managing large-scale projects. Our expertise is built on a foundation of technical knowledge and a dedicated approach to each case, ensuring that we not only meet but exceed the specific needs of our clients.

## Links
- [Twitter](https://twitter.com/your_project_twitter) - Follow us on Twitter for the latest updates.


## Table of Contents

- [Description](#description)
- [Modules](#modules)
  - [AI Model](#ai-model)
  - [SPL](#spl)
  - [Visualization](#Visualization)
  - [Workflow](#workflow)
- [Contributing](#contributing)
- [License](#license)

## Description

This repository contains tools and scripts for audio analysis, specifically focusing on sound visualization and level measurements. The project aims to extract and visualize various metrics from audio files, ensuring accurate representation and calibration.

## Modules

### AI Model

The AI Model directory contains machine learning models for audio analysis, including visualization tools and YAMNet, a deep learning model for sound event detection and classification.

### SPL

The SPL directory is dedicated to Sound Pressure Level (SPL) measurement analysis, including Leq levels and visualization tools.

#### Leq Levels

- `Leq_level`: Script for calculating Leq levels.
- `Leq_level_oct`: Script for octave band Leq level calculation.
- `Leq_level_oct_FFT`: Script for Leq level calculation with FFT.

### Visualization

- `Dash`: Dash app scripts for interactive visualization.

### Workflow

The Workflow directory contains diagrams and images that outline the audio analysis process and server setup.

- `AAC_Servers.drawio`: Diagram source file for server setup.

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change. Ensure to update tests as appropriate.

## License

All content is licensed under the terms of The Unlicense. For more information, please refer to [The Unlicense](https://unlicense.org).
