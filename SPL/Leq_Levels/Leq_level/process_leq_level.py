import os
import subprocess
# import logging
import logging

# usage example:

# (inference) PS C:\Users\GIS2\Documents\santi\GitHub\AAC\AI_Model\Urban_Model> python .\process_urban_model.py
# Enter the 3-Medidas folder: \\192.168.205.117\AAC_Server\PUERTOS\NOISEPORT\20231211_SANTUR\3-Medidas            

logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s', 
                    filename='leq_levels.log',
                    )

def process_audiomoth_folders(base_directory):
    for folder in os.listdir(base_directory):
        logging.info(f"There are {len(os.listdir(base_directory))} folders in {base_directory}")
        
        full_path = os.path.join(base_directory, folder)
        
        if os.path.isdir(full_path) and 'AUDIOMOTH' in os.listdir(full_path):
            audiopath = os.path.join(full_path, 'AUDIOMOTH')
            logging.info("Processing: " + audiopath)
            
            subprocess.run(['python', './leq_level_class.py', '-p', audiopath])

base_directory = input("Enter the 3-Medidas folder: ")
base_directory = os.path.join(base_directory)

process_audiomoth_folders(base_directory)
logging.info("Finished processing all folders")