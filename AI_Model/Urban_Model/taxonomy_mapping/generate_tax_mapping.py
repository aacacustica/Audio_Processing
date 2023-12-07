"""
Open the csv file and read the data in order to map the original classes 
with the AAC taxonomic. 
"""

import pandas as pd
import json
import subprocess

# get the last git tag version
def list_git_tags():
    try:
        tags = tags = subprocess.check_output(["git", "tag"]).strip().decode()
        return tags.split('\n')
    except subprocess.CalledProcessError:
        return None
    
tags = list_git_tags()

def select_tag(tags):
    for i, tag in enumerate(tags):
        print(f"{i}: {tag}")
    choice = int(input("Select the tag to use: "))
    
    return tags[choice]

version_tag = select_tag(tags)

# [1] Open the csv file and read the data
file_path = 'yamnet_class_AAC_301123.csv'
yamnet_classes = pd.read_csv(file_path, sep=';')
print(yamnet_classes.head())

# [2] Create a dictionary with the original classes name (display_name) as keys and the AAC classes (Brown_Level_1) as values
yamnet_classes_dict = {}
for i in range(len(yamnet_classes)):
    yamnet_classes_dict[yamnet_classes['display_name'][i]] = yamnet_classes['Brown_Level_2'][i]


print(f"\nThis is the taxonomy mapping:\n{yamnet_classes_dict}")
print(f"\n{len(yamnet_classes_dict)}")

# save the taxonomy mapping in a json file
with open(f'taxonomy_mapping_{version_tag}.json', 'w') as fp:
    json.dump(yamnet_classes_dict, fp)
print(f"\nFile taxonomy_mapping_{version_tag}.json saved!")

# print unique values of the new dictionary
print(f"\n{set(yamnet_classes_dict.values())}")
print(f"\n{len(set(yamnet_classes_dict.values()))}")