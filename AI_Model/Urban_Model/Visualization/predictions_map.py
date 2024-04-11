from utils import *
import os
import pandas as pd
import tqdm


def main():
    """
    python .\predictions_map.py -p ""
    """
    args = parse_arguments()
    stable_version = get_stable_version()

    ###############
    # Load data
    ###############
    # original audio classes
    yamnet_classes_path = r"C:\Users\scjaa\Documents\GitHubRepos\AAC\AI_Model\Urban_Model\yamnet_class_map.csv"
    yamnet_classes_df = pd.read_csv(yamnet_classes_path)
    yamnet_classes = yamnet_classes_df['display_name'].unique()
    # custom classes
    yammnet_class_map = r"C:\Users\scjaa\Documents\GitHubRepos\AAC\AI_Model\Urban_Model\taxonomy_mapping\yamnet_class_AAC_v2_0.csv"
    union = pd.read_csv(yammnet_class_map,sep=';')
    # taxonomy map
    urban_taxonomy_map = pd.read_json("urban_taxonomy_map_v1_0.json", typ='series').to_dict()

    folder_path = args.path
    subfolders = [f.path for f in os.scandir(folder_path) if f.is_dir()]

    csv_predictions_paths = []
    csv_leq_paths = []
    for subfolder in subfolders:
        prediction_path = os.path.join(subfolder, "AI_MODEL", "Predictions")
        leq_path = os.path.join(subfolder, "SPL")
        
        if not os.path.exists(prediction_path) or not os.path.exists(leq_path):
            print(f"Skipping {subfolder} as it does not contain the required folders")
            continue

        prediction_files = [os.path.join(prediction_path, f) for f in os.listdir(prediction_path) if f.endswith('.csv')]
        csv_predictions_paths.extend(prediction_files)
        leq_files = [os.path.join(leq_path, f) for f in os.listdir(leq_path) if f.endswith('.csv') and not 'oct' in f.lower() and '1_1' in f.lower()]
        csv_leq_paths.extend(leq_files)

    prediction_files = {}
    leq_files = {}
    for prediction_path in csv_predictions_paths:
        identifier = extract_identifier(prediction_path)
        prediction_files[identifier] = prediction_path

    for leq_path in csv_leq_paths:
        identifier = extract_identifier(leq_path)
        leq_files[identifier] = leq_path


    for identifier, prediction_path in tqdm.tqdm(prediction_files.items(), desc='Matching and Processing Files'):
        leq_path = leq_files.get(identifier)
        title = extract_location(prediction_path)  
        visualization_dir = output_dir(prediction_path)

        df = pd.read_csv(prediction_path)
        df = df.dropna()
        df_leq = pd.read_csv(leq_path)
        df_leq = df_leq.dropna()


        ###################
        # prediction map
        ###################
        df['Time'] = pd.to_datetime(df['Time'], format='%Y-%m-%d_%H:%M:%S')
        time_difference_seconds = df['Time'].diff().dt.total_seconds()
        average_interval = time_difference_seconds.mean()
        # interval_printing(average_interval)

        df['Processed_Class'] = df['Class'].apply(lambda x: match_classes(x, yamnet_classes))        
        df_exploded = df.explode('Processed_Class')
        # create a copied column of Time called Time_2
        df_exploded['Time_2'] = df_exploded['Time']
        df_exploded.set_index('Time', inplace=True)
        df_exploded = insert_dates(df_exploded)
        df_exploded['Mapped_Class'] = df_exploded['Processed_Class'].map(urban_taxonomy_map)


        ###################
        # tree_map
        ###################
        df_tree_map = df_exploded.copy()
        df_tree_map.rename(columns={'Filename':'filenames', 'Processed_Class':'Class_yamnet'}, inplace=True)
        df_tree_map['display_name'] = df_tree_map['Class_yamnet']
        df_tree_map['number'] = 1
        df_merged = df_tree_map.merge(union, how='left', on='display_name')
        df_merged = df_merged.loc[:, ~df_merged.columns.str.contains('^Unnamed')]
        df_merged = df_merged.drop(columns=['Brown_Level_1'])

        # Brown_Level_2, Brown_Level_3, NoisePort
        brown_2 = 'Brown_Level_2'
        brown_3 = 'Brown_Level_3'
        noiseport = 'NoisePort'

        # set what detail level to use
        original_classes = 'Class_yamnet'
        global_category = brown_2
        df_merged['TimeOfDay'] = df_merged['hour'].apply(categorize_time_of_day)
        # print(df_merged.columns)


        ###################
        # leq 
        ###################
        df_merged.rename(columns={'Time_2':'Time'}, inplace=True)
        df_leq['Time'] = pd.to_datetime(df_leq['Time'], format='%Y-%m-%d_%H:%M:%S')
        df_merge_leq = pd.merge_asof(df_merged, df_leq, on='Time', direction='nearest')
        df_merge_leq = df_merge_leq.drop(columns=['Filename'])


        ################# 
        #plot
        #################
        plot_prediction_map(df_exploded, title, visualization_dir, stable_version)
        plot_stack_bar(df_exploded, title, visualization_dir, stable_version)
        plot_tree_map(df_merged, global_category, original_classes, title, visualization_dir, stable_version)
        plot_aggregated_tree_map(df_merged, global_category, original_classes, title, visualization_dir, stable_version)
        plot_leq_pred(df_merge_leq, global_category, original_classes, title, visualization_dir, stable_version)

if __name__ == '__main__':
    main()
