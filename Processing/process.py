import os
import subprocess
import logging

logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s', 
                    filename='processing.log',
                    )

###############################################################
###############################################################
###############################################################
# PROCESSING AI MODEL

# usage example:
#     (inference) PS C:\Users\GIS2\Documents\santi\GitHub\AAC\AI_Model\Urban_Model> python .\process_urban_model.py
#     Enter the 3-Medidas folder: \\192.168.205.117\AAC_Server\PUERTOS\NOISEPORT\20231211_SANTUR\3-Medidas

def process_urban_model(base_directory):
    for folder in os.listdir(base_directory):
        logging.info(f"There are {len(os.listdir(base_directory))} folders in {base_directory}")
        
        full_path = os.path.join(base_directory, folder)
        
        if os.path.isdir(full_path) and 'AUDIOMOTH' in os.listdir(full_path):
            audiopath = os.path.join(full_path, 'AUDIOMOTH')
            logging.info("Processing: " + audiopath)
            
            subprocess.run(['python', './urban_model.py', '-p', audiopath])

logging.info("Starting processing LEQ LEVELS")

# go to path
os.chdir(r'C:\\Users\\GIS2\\Documents\\santi\\GitHub\\AAC\\\AI_Model\\Urban_Model')

base_directory = input("Enter the 3-Medidas folder: ")
base_directory = os.path.join(base_directory)

process_urban_model(base_directory)

###############################################################
###############################################################
###############################################################

# PROCESSING LEQ LEVELS
def process_leq_level(base_directory):
    for folder in os.listdir(base_directory):
        full_path = os.path.join(base_directory, folder)
        
        if os.path.isdir(full_path) and 'AUDIOMOTH' in os.listdir(full_path):
            audiopath = os.path.join(full_path, 'AUDIOMOTH')
            logging.info("Processing: " + audiopath)
            
            subprocess.run(['python', './leq_level_class.py', '-p', audiopath])

logging.info("Starting processing LEQ LEVELS")
# go to path
os.chdir(r'C:\\Users\\GIS2\\Documents\\santi\\GitHub\\AAC\\\SPL\\Leq_Levels\\Leq_level')

process_leq_level(base_directory)


###############################################################
###############################################################
###############################################################

# PLOTTING LEQ LEVELS
def process_plotting(base_directory):
    subprocess.run(['python', './main.py', '-f', base_directory, '-a', '900', '-p', '90', '10'])

logging.info("Starting plotting leq levels")
# go to path
os.chdir(r'C:\\Users\\GIS2\\Documents\\santi\\GitHub\\AAC\\\SPL\\Visualization\\Sonometer-AudioMoth')

base_directory_plot = base_directory.replace('3-Medidas', '5-Resultados')
process_plotting(base_directory)