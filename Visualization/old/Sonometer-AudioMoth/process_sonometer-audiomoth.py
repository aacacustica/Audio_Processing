import os
import subprocess
import logging

logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s', 
                    filename='sonometer-audiomoth.log',
                    )

# PLOTTING LEQ LEVELS
# def process_plotting(base_directory):
#     for folder in os.listdir(base_directory):
#         full_path = os.path.join(base_directory, folder)
        
#         if os.path.isdir(full_path) and 'SPL' in os.listdir(full_path):
#             audiopath = os.path.join(full_path, 'SPL')
#             logging.info("Processing: " + audiopath)
            
#             subprocess.run(['python', './main.py', '-f', audiopath, '-a', '900', '-p', '90', '10'])

def process_plotting(base_directory):
    subprocess.run(['python', './main.py', '-f', base_directory, '-a', '900', '-p', '90', '10'])


logging.info("Starting plotting leq levels")
# go to path
# os.chdir(r'C:\\Users\\GIS2\\Documents\\santi\\GitHub\\AAC\\\SPL\\Visualization\\Sonometer-AudioMoth')
# python .\main.py -f "\\192.168.205.117\AAC_Server\INDUSTRIA\23132-IRUÑA_OCA_CANTERA\5-Resultados

base_directory = input("Enter the 5-Resultados folder: ")
process_plotting(base_directory)