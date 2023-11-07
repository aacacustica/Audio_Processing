# Workflow Overview

This directory contains diagrams and documentation outlining the audio data processing workflow from collection to final storage. The purpose is to provide clarity on the process involved in handling audio records, their temporary and permanent storage, and the role of GitHub in maintaining and accessing our processing scripts.

## Workflow Objective

![AAC_workflow](https://github.com/santiagocampojurado/AAC/assets/89314673/3cb6080f-d0ec-4c6f-a126-08495eed9038)


The primary objective of this workflow is to establish a clear and uniform methodology that can be easily followed and referenced by any team member at any time. Our workflow encapsulates three key stages:

- **Audio Collection**
- **Audio File Processing**
- **Uploading Verified Results**

We will integrate three principal components within our workflow:

- **The Hard Drive:** Serves as the central repository for all audio data, ensuring that every piece of audio content is accounted for and securely stored.

- **The Local Server:** Designated as our 'laboratory,' the Local Server is where we will process audio files and address any emerging issues. 

- **Personal Computers:** It is crucial to emphasize that **audio processing will always be performed on personal computers**. This measure ensures the integrity of the original audio files and the optimization of processing power.

Once the results have been verified, they will be uploaded to the designated storage system. We aim to maintain a consistent infrastructure from the collection of audio data to the final stage of result verification, facilitating a seamless operational process for the team.


## Local Server Purpose

The Local Server serves a dual purpose:

1. To temporarily store audio for processing.
2. To keep the results until they are validated.

Once the processing is complete and the results are confirmed by team members (Ainhoa, Nefersson, Alberto, etc.), they will be transferred to the Microsoft Server (SharePoint) for permanent storage. Subsequently, they will be deleted from the Local Server.

## GitHub Repository

The GitHub repository's purpose is to enhance control and access to our programs. I will manage the updates and uploads of stable versions used for audio processing. In addition to their presence in the repo, these stable versions will also be available on the Microsoft Server (SharePoint). Specific locations will be communicated as updates are made. If you are familiar with Git, you are encouraged to collaborate directly through forks and pull requests to propose code improvements. Alternatively, you can reach out to me directly with any suggestions.

## Detailed Workflow:

![AAC_Servers_and_workflow](https://github.com/santiagocampojurado/AAC/assets/89314673/1b71480a-1e39-4b5e-b476-5b79f56b8f3f)

- **Audio Collection**: Records will be downloaded and uploaded to the AAC_BOOK hard drive, maintaining the current storage structure by folder (year, Leisure/Traffic..., project, etc.). Suggestions for improving this structure are welcome.

- **Processing Audios**: New audios intended for processing will be uploaded to the Local Server (192.168.205.117). The structure here should mirror that of the Microsoft Server (SharePoint) to ensure consistency and ease of handling. NOTE: AUDIOS ARE NOT PROCESSED ON THE LOCAL SERVER. It will function as a 'laboratory' to store results from our PCs, thus preventing any possible corruption of the original audio files.

- **Result Verification**: After results are verified, they will be uploaded to the corresponding file on the Microsoft Server (SharePoint) and then deleted from the Local Server (both audios and results).



The replication of the SharePoint structure on the Local Server will facilitate the management and location of final results. This methodology will also optimize space management. Additionally, I will implement a documentation system to record the version of the program used in each audio process. This information will be included in the results, allowing for precise reprocessing in the future if necessary.


## Processing Detail Explanation

![AAC_workflow](https://github.com/santiagocampojurado/AAC/assets/89314673/c05da2e0-2d72-4625-be99-605ccc089954)

## Main Audio Processing Activities

Our audio analysis framework is structured around three primary activities, each encompassing unique processes and visualization techniques:

### 1) Leq Levels

Leq Levels is an area where we explore three distinct approaches to audio analysis:

- **Leq levels**: The basic measurement of sound pressure level over a period.
- **1/3 Octave**: A more detailed frequency analysis within the one-third octave bands.
- **1/3 Octave with FFT**: Incorporates Fast Fourier Transform for a comprehensive frequency domain analysis.

Within Leq Levels, we employ three types of visualizations:

- **Dash Plots**: Utilize Dash to create interactive plots of desired levels and frequencies.
- **Spectrograms**: Visualize the sound frequency and its variance over time.
- **Heat Map Levels**: Generate heat maps to represent decibel levels across time intervals.

### 2) AI Noise Model

The AI Model activity employs the YAMNet model for sound event detection:

- **Prediction Phase**: We process the audio to predict sound events, which can range from 1 to 10 different predictions, depending on the audio's length. The window size for analysis is adjustable based on the audio duration.
- **Peak Analysis**: By setting a threshold informed by SPL analysis, we extract 5-second clips from portions of the audio that exceed this limit.

The AI Model offers various visualization tools:

- **Heat Map Prediction**: Visualize the predictions' distribution over time.
- **Dash Board Brown Level**: This dashboard allows us to delve into the categories of sounds, identifying predominant ones and examining sub-categories for detailed insights.
- **Temporal Analysis**: We use this tool to analyze patterns across different timescales, such as days, hours, months, and years, providing a granular view of the data.

### 3) Sonometer

The Sonometer analysis parallels the Leq Levels in terms of process but is more detailed. The specifics of this activity will be elaborated upon in the future, as my familiarity with the Sonometer's technicalities grows.



