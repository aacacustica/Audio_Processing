# Workflow Overview

This directory contains diagrams and documentation outlining the audio data processing workflow from collection to final storage. The purpose is to provide clarity on the process involved in handling audio records, their temporary and permanent storage, and the role of GitHub in maintaining and accessing our processing scripts.

## Local Server Purpose

The Local Server serves a dual purpose:

1. To temporarily store audio for processing.
2. To keep the results until they are validated.

Once the processing is complete and the results are confirmed by team members (Ainhoa, Nefersson, Alberto, etc.), they will be transferred to the Microsoft Server (SharePoint) for permanent storage. Subsequently, they will be deleted from the Local Server.

## GitHub Repository

The GitHub repository's purpose is to enhance control and access to our programs. I will manage the updates and uploads of stable versions used for audio processing. In addition to their presence in the repo, these stable versions will also be available on the Microsoft Server (SharePoint). Specific locations will be communicated as updates are made. If you are familiar with Git, you are encouraged to collaborate directly through forks and pull requests to propose code improvements. Alternatively, you can reach out to me directly with any suggestions.

## Detailed Workflow:

![AAC_workflow](https://github.com/santiagocampojurado/AAC/assets/89314673/e2558b4a-abdb-4f62-b5b5-470d90597ebc)


- **Audio Collection**: Records will be downloaded and uploaded to the AAC_BOOK hard drive, maintaining the current storage structure by folder (year, Leisure/Traffic..., project, etc.). Suggestions for improving this structure are welcome.

- **Processing Audios**: New audios intended for processing will be uploaded to the Local Server (192.168.205.117). The structure here should mirror that of the Microsoft Server (SharePoint) to ensure consistency and ease of handling. NOTE: AUDIOS ARE NOT PROCESSED ON THE LOCAL SERVER. It will function as a 'laboratory' to store results from our PCs, thus preventing any possible corruption of the original audio files.

- **Result Verification**: After results are verified, they will be uploaded to the corresponding file on the Microsoft Server (SharePoint) and then deleted from the Local Server (both audios and results).


![AAC_Servers_and_workflow](https://github.com/santiagocampojurado/AAC/assets/89314673/1b71480a-1e39-4b5e-b476-5b79f56b8f3f)


The replication of the SharePoint structure on the Local Server will facilitate the management and location of final results. This methodology will also optimize space management. Additionally, I will implement a documentation system to record the version of the program used in each audio process. This information will be included in the results, allowing for precise reprocessing in the future if necessary.

