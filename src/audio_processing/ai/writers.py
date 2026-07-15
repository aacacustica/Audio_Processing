import os
import pandas as pd


def save_predictions_to_csv(all_data_subfolder, col_names, subfolder_name, subfolder, model_type, logging, window_size=None, stable_version=None):
    logging.info("")
    if window_size is not None:
        if model_type == "port":
            output_filename = f'Port_Model_{subfolder_name}_w_{window_size}s_{stable_version}.csv'
        else:
            output_filename = f'Urban_Model_{subfolder_name}_w_{window_size}s_{stable_version}.csv'
    else:
        if model_type == "port":
            output_filename = f'Port_Model_{subfolder_name}_{stable_version}.csv'
        else:
            output_filename = f'Urban_Model_{subfolder_name}_{stable_version}.csv'
    
    subfolder = subfolder.replace('3-Medidas', '5-Resultados')
    output_folder = os.path.join(subfolder, 'AI_MODEL', 'Predictions')

    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    output_full_path = os.path.join(output_folder, output_filename)

    df_subfolder = pd.DataFrame(all_data_subfolder, columns=col_names)
    # order df by date
    df_subfolder = df_subfolder.sort_values(by='date')
    df_subfolder.to_csv(output_full_path, index=False)
    logging.info(f'Output saved to {output_full_path}')
