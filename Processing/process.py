import os
import subprocess
import logging
import sys

# python .\process.py \\192.168.205.117\AAC_Server\TEST\3-Medidas

logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s', 
                    filename='processing.log')

def run_subprocess(command):
    try:
        logging.info(f"Running command: {' '.join(command)}")
        subprocess.run(command, check=True)
        logging.info("Command finished successfully.")
    except subprocess.CalledProcessError as e:
        logging.error(f"An error occurred while running command: {e}")

urban_model_program = 'urban_model.py'
leq_level_program = 'leq_level_class.py'
plotting_program = 'main.py'

def get_last_subfolder(directory):
    subfolders = [os.path.join(directory, o) for o in os.listdir(directory) 
                  if os.path.isdir(os.path.join(directory, o))]
    if not subfolders:
        return None
    # Sort subfolders by name and return the last one
    subfolders.sort()
    return subfolders[-1]

def process_urban_model(base_directory):
    os.chdir(r'C:\Users\GIS2\Documents\santi\GitHub\AAC\AI_Model\Urban_Model')
    logging.info("Changed directory to Urban Model")
    logging.info(f"There are {len(os.listdir(base_directory))} folders to process in Urban Model")
    
    for folder in os.listdir(base_directory):
        logging.info(f"Processing folder: {folder}")
        full_path = os.path.join(base_directory, folder)
        if os.path.isdir(full_path):
            last_subfolder = get_last_subfolder(full_path)
            if last_subfolder:
                logging.info(f"Found last subfolder in {full_path}. Processing...")
                subprocess.run(['python', urban_model_program, '-p', last_subfolder])

def process_leq_level(base_directory):
    os.chdir(r'C:\Users\GIS2\Documents\santi\GitHub\AAC\SPL\Leq_Levels\Leq_level')
    logging.info("Changed directory to Leq Level")
    for folder in os.listdir(base_directory):
        full_path = os.path.join(base_directory, folder)
        if os.path.isdir(full_path):
            last_subfolder = get_last_subfolder(full_path)
            if last_subfolder:
                logging.info(f"Processing: {last_subfolder} in Leq Level")
                run_subprocess(['python', leq_level_program, '-p', last_subfolder])
            
def process_plotting(base_directory):
    os.chdir(r'C:\Users\GIS2\Documents\santi\GitHub\AAC\SPL\Visualization\Sonometer-AudioMoth')
    logging.info("Changed directory to Plotting")
    base_directory_plot = base_directory.replace('3-Medidas', '5-Resultados')
    logging.info(f"Processing plotting for: {base_directory_plot}")
    run_subprocess(['python', plotting_program, '-f', base_directory_plot, '-a', '900', '-p', '90', '10'])

if __name__ == "__main__":
    if len(sys.argv) != 2:
        logging.error("Incorrect number of arguments passed.")
        print("Usage: python script.py <3-Medidas folder path>")
        sys.exit(1)

    base_directory = sys.argv[1]
    if not os.path.exists(base_directory):
        logging.error(f"The provided path does not exist: {base_directory}")
        print(f"The provided path does not exist: {base_directory}")
        sys.exit(1)

    logging.info("Starting processing AI MODEL")
    process_urban_model(base_directory)

    logging.info("Starting processing LEQ LEVELS")
    process_leq_level(base_directory)

    logging.info("Starting plotting leq levels")
    process_plotting(base_directory)
