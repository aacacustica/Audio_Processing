import os
import subprocess
import logging

logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s', 
                    filename='processing.log')

def process_stage(base_directory, process_function):
    for folder in os.listdir(base_directory):
        logging.info(f"There are {len(os.listdir(base_directory))} folders in {base_directory}")
        
        full_path = os.path.join(base_directory, folder)
        
        if os.path.isdir(full_path) and 'AUDIOMOTH' in os.listdir(full_path):
            audiopath = os.path.join(full_path, 'AUDIOMOTH')
            logging.info(f"Processing: {audiopath}")
            
            process_function(audiopath)

def process_urban_model(audiopath):
    subprocess.run(['python', './urban_model.py', '-p', audiopath])

def process_leq_level(audiopath):
    subprocess.run(['python', './leq_level_class.py', '-p', audiopath])

def process_plotting(audiopath):
    subprocess.run(['python', './main.py', '-f', audiopath, '-a', '900', '-p', '90', '10'])

base_directory = input("Enter the 3-Medidas folder: ")
base_directory = os.path.join(base_directory)

# Processing AI Model
logging.info("Starting processing AI MODEL")
os.chdir(r'C:\\Users\\GIS2\\Documents\\santi\\GitHub\\AAC\\AI_Model\\Urban_Model')
process_stage(base_directory, process_urban_model)

# Processing LEQ Levels
logging.info("Starting processing LEQ LEVELS")
os.chdir(r'C:\\Users\\GIS2\\Documents\\santi\\GitHub\\AAC\\SPL\\Leq_Levels\\Leq_level')
process_stage(base_directory, process_leq_level)

# Processing Plotting
logging.info("Starting plotting leq levels")
os.chdir(r'C:\\Users\\GIS2\\Documents\\santi\\GitHub\\AAC\\SPL\\Visualization\\Sonometer-AudioMoth')
process_stage(base_directory, process_plotting)
