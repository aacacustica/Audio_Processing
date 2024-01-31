## Launching GUI Processing

### Overview
`Purpose:` Automates the execution of processes related to audio data processing.
`GUI Framework:` Tkinter.
`Subprocess Management:` Uses subprocess module to run external scripts.
`Logging and Output:` Displays logs and subprocess outputs in the GUI.


### Key Components
`TextHandler (Class):` A custom logging handler to redirect logs to a Tkinter Text widget.

### Subprocess Execution Functions:
- `run_subprocess:` Executes a given command as a subprocess and captures its output.
- `process_urban_model:` Processes audio data using the 'Urban Model' script.
- `process_leq_level:` Processes audio data using the 'Leq Level' script.
- `process_plotting:` Generates plots based on the processed data using a plotting script.


### Utility Functions:
- `get_last_subfolder:` Retrieves the last subfolder in a given directory.
- `process_in_thread:` Manages the execution of the above processes in a separate thread.
- `start_processing:` Starts the processing thread based on user input.
- `check_queue:` Periodically checks and updates the GUI with messages from the processing thread.
- `browse_folder:` Opens a file dialog to select a directory and normalizes the selected path.


### User Interface
- `Entry Field:` Allows the user to enter or select a directory path.

### Buttons:
- `"Browse":` Opens a directory selection dialog.
- `"Start Processing":` Initiates the processing of audio data.
- `Log Display:` A scrolled text area to display the processing logs and status updates.


### Execution Flow
The user enters or selects a directory path.
Upon clicking `"Start Processing"`, the script:

- Validates the path.
- Initiates subprocesses in a separate thread for processing audio data in three stages: Urban Model, Leq Level, and Plotting.
- Logs and messages from these subprocesses are displayed in the GUI.

### External Scripts
- `urban_model_program:` `'urban_model.py'`
- `leq_level_program:` `'leq_level_class.py'`
- `plotting_program:` `'main.py'`


### Error Handling
The script handles subprocess errors and general exceptions, displaying error messages in the GUI.


### Note
The script assumes certain directory structures and relies on specific external Python scripts (`urban_model.py`, `leq_level_class.py`, `main.py`).
The actual processing logic and data handling are in the external scripts mentioned.