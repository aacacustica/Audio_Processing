import pandas as pd
import json
import subprocess
import argparse
from distutils.version import LooseVersion


# CONSTANTS
# column to be the VALUE in the dictionary
brown_2 = 'Brown_Level_2'
brown_3 = 'Brown_Level_3'

noise_1 = 'NoisePort_Level_1'
noise_2 = 'NoisePort_Level_2'

VALUE_COLUMN = noise_2
TAXONOMY_NAME = 'taxonomy_mapping'
YAMNET_CLASS_AAC = r"C:\Users\scjaa\AAC - CENTRO DE ACUSTICA APLICADA, S.L\I + D + i - Documentos\Modelos_IA\AAC_IA_Puerto\yamnet_class_AAC_v3_0.csv"


# get the last git tag version
def list_git_tags():
    try:
        tags = subprocess.check_output(["git", "tag"]).strip().decode()
        sorted_tags = sorted(tags.split('\n'), key=LooseVersion)
        return sorted_tags
    except subprocess.CalledProcessError:
        return None
    

def select_tag(tags):
    for i, tag in enumerate(tags):
        print(f"{i}: {tag}")
    choice = int(input("Select the tag to use: "))
    
    return tags[choice]


def get_latest_tag(tags):
    if tags:
        return tags[-1]  #latest tag
    else:
        return None


def argument_parser():
    parser = argparse.ArgumentParser(description='Generate the taxonomy mapping for the AAC classes')
    parser.add_argument('-f', '--file_path_yamnet', type=str, required=False, default=YAMNET_CLASS_AAC, help='Path to the csv file with the YAMNet classes')
    parser.add_argument('-n', '--filename_taxonomy', type=str, default=TAXONOMY_NAME, help='Name of the taxonomy mapping file')
    parser.add_argument('--column', type=str, default=VALUE_COLUMN, help='Column to be used as the VALUE in the dictionary')
    args = parser.parse_args()
    return args


def main():
    """
    python .\generate_tax_mapping.py -n port_2
    """
    
    args = argument_parser()
    tags = list_git_tags()
    version_tag = get_latest_tag(tags)
    file_path = args.file_path_yamnet
    name = args.filename_taxonomy
    column = args.column

    # [1] Open the csv file and read the data
    yamnet_classes = pd.read_csv(file_path, sep=';')
    # remove Brown_Level_1 column and any Unnamed columns
    yamnet_classes = yamnet_classes.drop(columns=['Brown_Level_1'])
    yamnet_classes = yamnet_classes.loc[:, ~yamnet_classes.columns.str.contains('^Unnamed')]

    # save the csv file without the Brown_Level_1 column
    path_csv = YAMNET_CLASS_AAC.split('\\')[:-1]
    csv_filename = YAMNET_CLASS_AAC.split('\\')[-1].replace('.csv', '_clean.csv')
    csv_filename = '\\'.join(path_csv) + '\\' + csv_filename
    yamnet_classes.to_csv(f'{csv_filename}', sep=';', index=False)


    # [2] Create a dictionary with the original classes name (display_name) as keys and the AAC classes (Brown_Level_1) as values
    yamnet_classes_dict = {}
    for i in range(len(yamnet_classes)):
        yamnet_classes_dict[yamnet_classes['display_name'][i]] = yamnet_classes[VALUE_COLUMN][i]

    print(f"\n{len(yamnet_classes_dict)}")


    # save the taxonomy mapping in a json file
    if name == TAXONOMY_NAME:
        with open(f'{name}_{version_tag}.json', 'w') as fp:
            json.dump(yamnet_classes_dict, fp)
            print(f"\nFile {name}_{version_tag}.json has been created")
    else:
        with open(f'{name}_{TAXONOMY_NAME}_{version_tag}.json', 'w') as fp:
            json.dump(yamnet_classes_dict, fp)
            print(f"\nFile {name}_{TAXONOMY_NAME}_{version_tag}.json has been created")
    # print unique values of the new dictionary
    print(f"\n{set(yamnet_classes_dict.values())}")
    print(f"\n{len(set(yamnet_classes_dict.values()))}")


if __name__ == '__main__':
    main()