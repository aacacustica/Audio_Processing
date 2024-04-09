import os
import subprocess
import argparse
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.patches import Patch
import plotly.express as px
import numpy as np
import matplotlib.colors as mcolors

# Constants
MIN_5 = 320
MIN_10 = 620
MIN_15 = 1000
MIN_30 = 1820
MIN_60 = 3620
MIN_120 = 7220

COLLOR_PALLET_URBAN = {
            'Other human': '#2986cc', # BLUE
            'Electro-mechanical': '#cc0000', # RED
            'Voice': '#6aa84f', #  green 6aa84f
            'Motorised transport': '#ffa500', # orange
            'Geonature': '#8e7cc3', # PURPLE
            'Animal': '#9b5f00', # BROWN
            'Music': '#d172a4', # PINK
            'Background': '#000000', # BLACK
            'Other Sounds': '#c9d631', # yellow
            'Social/communal': '#d8cbf8', # Light purple
            'Human movement': '#40b674', # light green 40b674
        }

COLOR_PALLET_L2 = {
            'Other human': '#2986cc', # BLUE
            'Electro-mechanical': '#cc0000', # RED
            'Voice': '#6aa84f', #  green 6aa84f
            'Motorised transport': '#ffa500', # orange
            'Geonature': '#8e7cc3', # PURPLE
            'Animal': '#9b5f00', # BROWN
            'Music': '#d172a4', # PINK
            'Background': '#000000', # BLACK
            'Other Sounds': '#c9d631', # yellow
            'Social/communal': '#d8cbf8', # Light purple
            'Human movement': '#40b674', # light green 40b674
        }


cmap_dict = sns.color_palette(palette=["#C8FFC8", "#00C800", "#007800", "#FFFF00", "#FFC878", "#FF9600", "#FF0000", "#780000", "#FF00FF", "#8C3CFF", "#000078"], n_colors=11)
hex_colors = [mcolors.to_hex(color) for color in cmap_dict]
custom_color_scale = [[i/len(hex_colors), color] for i, color in enumerate(hex_colors)]
custom_color_scale.append([1, hex_colors[-1]])



def parse_arguments():
    parser = argparse.ArgumentParser(description='Make prediction with YAMNet model for audio files in a directory')
    parser.add_argument('-p', '--path', type=str, required=True, help='Directory to be processed')
    parser.add_argument('-w', '--window_size', type=float, default=None, help='Window size in seconds for processing audio files. Default is None for processing full audio.')
    return parser.parse_args()


def extract_location(file_path):
    file_name = os.path.basename(file_path)
    file_name = file_name.replace("predictions_", "")
    parts = file_name.split("_")
    location = "_".join(parts[:2])
    return location


def remove_label(classes_list, label):
    return [x for x in classes_list if x != label]


def change_label(classes_list, label, new_label):
    return [new_label if x == label else x for x in classes_list]


def first_element(classes_list):
    return [classes_list[0]] if classes_list else []


def interval_printing(average_interval):
    if average_interval > 0 and average_interval < MIN_5:
        print(f"The average interval between each audio file is 5 minutes ({round(average_interval)} seconds, which are {round(average_interval/60)} minutes)")
    elif average_interval > MIN_5 and average_interval < MIN_10:
        print(f"The average interval between each audio file is 10 minutes ({round(average_interval)} seconds, which are {round(average_interval/60)} minutes)")
    elif average_interval > MIN_10 and average_interval < MIN_15:
        print(f"The average interval between each audio file is 15 minutes ({round(average_interval)} seconds, which are {round(average_interval/60)} minutes)")
    elif average_interval > MIN_15 and average_interval < MIN_30:
        print(f"The average interval between each audio file is 30 minutes ({round(average_interval)} seconds, which are {round(average_interval/60)} minutes)")
    elif average_interval > MIN_30 and average_interval < MIN_60:
        print(f"The average interval between each audio file is 60 minutes ({round(average_interval)} seconds), which are {round(average_interval/60)} minutes)")
    elif average_interval > MIN_60 and average_interval < MIN_120:
        print(f"The average interval between each audio file is 120 minutes ({round(average_interval)} seconds, which are {round(average_interval/60)} minutes)")


def insert_dates(df):
    df['date'] = df.index.date
    df["year"] = df.index.year
    df["month"] = df.index.month
    df["day"] = df.index.day
    df["hour"] = df.index.hour
    df["minute"] = df.index.minute
    df["second"] = df.index.second
    df["weekday"] = df.index.day_name()

    weekday_translation = {
        "Monday": " Lunes",
        "Tuesday": " Martes",
        "Wednesday": " Miércoles",
        "Thursday": " Jueves",
        "Friday": " Viernes",
        "Saturday": " Sábado",
        "Sunday": " Domingo"
    }

    df["weekday"] = df["weekday"].replace(weekday_translation)
    df["weekday"] = df["weekday"].astype(str)
    df["day"] = df["day"].astype(str).str.zfill(2)
    df["fullday"] = df["day"] + df["weekday"]
    return df


def output_dir(path: str):
    path = os.path.abspath(path).split("\\")[:-2]
    path = "/".join(path)
    
    visualization_dir = path + "/Visualizations"
    os.makedirs(visualization_dir, exist_ok=True)
    return visualization_dir


def list_git_tags():
    try:
        tags = tags = subprocess.check_output(["git", "tag"]).strip().decode()
        return tags.split('\n')
    except subprocess.CalledProcessError:
        return None
    
def select_tag(tags):
    for i, tag in enumerate(tags):
        print(f"{i}: {tag}")
    choice = int(input("Select the tag to use: "))
    tag_selected = tags[choice]
    # replace "." with "_" to be able to use it as a file name
    tag_selected = tag_selected.replace(".", "_")
    return tag_selected

def get_stable_version():
    tags = list_git_tags()
    # get the latest stable version
    tag_selected = tags[-1]
    # print(f"Latest stable version: {tag_selected}")
    # replace "." with "_" to be able to use it as a file name
    tag_selected = tag_selected.replace(".", "_")
    # print(f"Latest stable version: {tag_selected}")
    return tag_selected

def match_classes(class_label, yamnet_classes):
    parts = class_label.split(',')
    matched_classes = []
    i = 0

    while i < len(parts):
        part = parts[i].strip()
        if part in yamnet_classes:
            matched_classes.append(part)
            i += 1
            continue

        if i + 1 < len(parts):
            composite_candidate = f"{part}, {parts[i+1].strip()}"
            if composite_candidate in yamnet_classes:
                matched_classes.append(composite_candidate)
                i += 2
                continue
        i += 1
    return matched_classes


def info_test(df_exploded):
    unique_classes = df_exploded['Mapped_Class'].unique()
    print("Unique classes in processed_class: ", unique_classes)
    print("Total unique classes in processed_class: ", len(unique_classes))
    print("Count of each class in processed_class: ", df_exploded['Mapped_Class'].value_counts())


def map_classes_to_taxonomy(classes, mapping):
    mapped = [mapping.get(cls, cls) for cls in classes]
    return mapped


def categorize_time_of_day(hour):
    if 7 <= hour < 19:
        return 'Ld'
    elif 19 <= hour < 23:
        return 'Le'
    else:
        return 'Ln' 


def leq(levels):
    levels = levels[~np.isnan(levels)]
    l = np.array(levels)
    return 10 * np.log10(np.mean(np.power(10, l / 10)))


def extract_identifier(filename):
    base_name = os.path.basename(filename)
    parts = base_name.split('_')
    if 'predictions' in base_name:
        identifier = '_'.join(parts[1:3])
    else:
        identifier = '_'.join(parts[2:4])
    return identifier


def plot_prediction_map(df, title, visualization_dir, stable_version):
    df = df.sort_values(by=["year", "month", "fullday"])
    # map class to number
    class_to_num = {class_name: index+1 for index, class_name in enumerate(df['Mapped_Class'].unique())}
    df['class_num'] = df['Mapped_Class'].map(class_to_num)

    # inverting the dictionary to get the name of the class for the legend
    name_class = {v: k for k, v in class_to_num.items()}

    # mapping from classes numbers to colors
    num_to_color = {num: COLLOR_PALLET_URBAN[class_name] for class_name, num in class_to_num.items()}
    cmap = [num_to_color[cls_num] for cls_num in name_class.keys()]

    # leggend elements colors
    legend_elements = [Patch(facecolor=num_to_color[cls_num], label=f"Clase {cls_num} - {name_class.get(cls_num, '')}") for cls_num in name_class.keys()]

    day_class = pd.pivot_table(data=df, columns=df.index.time, index=["year", "month", "fullday"], values="class_num", aggfunc='mean')

    plt.figure(figsize=(45, 35))

    if day_class.isna().all().all() or day_class.empty:
        print("No valid data. Skipping...")
        
    else:
        ax = sns.heatmap(day_class, annot=False, cmap=cmap, linewidth=0.5, cbar=False)
        
        ax.set_xticks(range(len(day_class.columns)))
        ax.set_xticklabels([t.strftime('%H:%M:%S') for t in day_class.columns], rotation=90)
        
        yticklabels = [f"{idx[0]}-{idx[1]}-{idx[2]}" for idx in day_class.index]
        ax.set_yticklabels(yticklabels, rotation=0)
        
        plt.legend(handles=legend_elements, title="Clases", loc='center left', bbox_to_anchor=(1, 0.5))
        plt.title(f"{title} | Clases por día y hora")
        plt.plot()

        plt.savefig(f"{visualization_dir}/{title}_predictions_map_{stable_version}.png", bbox_inches='tight')
        print(f"Saved image at {visualization_dir}/{title}_predictions_map_{stable_version}.png")
    # plt.show()



def plot_stack_bar(df_explode, title, visualization_dir, stable_version):
    df_explode.rename(columns={"fullday": "Día", "hour": "Hora"}, inplace=True)
    unique_día_weekday = df_explode['Día'].unique()

    df_explode['Día'] = pd.Categorical(df_explode['Día'], categories=unique_día_weekday, ordered=True)
    dfg = df_explode.groupby(['Mapped_Class', 'Día'], observed=True).count().reset_index()

    fig = px.bar(
        dfg, 
        x='Día',
        y='Processed_Class',
        color='Mapped_Class',
        title=f'{title} | Clases por día',
        color_discrete_sequence=px.colors.qualitative.Alphabet, 
        color_discrete_map=COLLOR_PALLET_URBAN,
        height=900,
        width=2000
    )

    # save plot
    fig.write_html(f"{visualization_dir}/{title}_classes_per_day_{stable_version}.html")
    print(f"Saving image at {visualization_dir}/{title}_classes_per_day_{stable_version}.html")
    

def plot_tree_map(df, global_category, original_classes, title, visualization_dir, stable_version):
    fig = px.treemap(df, 
                 path=[global_category, original_classes], 
                 values='number',
                 color=global_category,  #for coloring
                 color_discrete_map=COLLOR_PALLET_URBAN,
                )

    fig.update_layout(title=f'{title} Global | Urban Model | From {df["date"].iloc[0]} to {df["date"].iloc[-1]}')
    fig.show()

    fig.write_html(f"{visualization_dir}/{title}_Global_UrbanModel_{stable_version}.html")

    # plot each day
    for day in df['date'].unique():
        df_day = df[df['date'] == day]
        fig = px.treemap(df_day, 
                 path=[global_category, original_classes], 
                 values='number',
                 color=global_category,  #for coloring
                 color_discrete_map=COLLOR_PALLET_URBAN,
                )

        fig.update_layout(title=f'{title} | Urban Model | {day}')
        fig.show()

        fig.write_html(f"{visualization_dir}/{title}_UrbanModel_{day}_{stable_version}.html")
        print(f"Saving image at {visualization_dir}/{title}_UrbanModel_{day}_{stable_version}.html")


def plot_aggregated_tree_map(df, global_category, original_classes, title, visualization_dir, stable_version):
    df_grouped = df.groupby([global_category, original_classes, 'TimeOfDay']).agg({'number':'sum'}).reset_index()
    
    fig = px.treemap(df_grouped, 
                     path=['TimeOfDay', global_category, original_classes],
                     values='number',
                     color=global_category,  #for coloring
                     color_discrete_map=COLLOR_PALLET_URBAN,
                    )

    fig.update_layout(title=f'{title} | Urban Model | Time Periods | From {df["date"].iloc[0]} to {df["date"].iloc[-1]}')
    fig.show()

    fig.write_html(f"{visualization_dir}/{title}_UrbanModel_TimePeriods_{stable_version}.html")
    print(f"Saving image at {visualization_dir}/{title}_UrbanModel_TimePeriods_{stable_version}.html")



def plot_leq_pred(df_merge_leq, global_category, title, visualization_dir, stable_version):
    grouped_df = df_merge_leq.groupby(global_category).agg(
    number=('Class_yamnet', 'size'),
    LAeq=('LA', lambda x: leq(x))
    ).reset_index()

    fig = px.treemap(grouped_df, 
                    path=[global_category],  
                    values='number',
                    color='LAeq',
                    color_continuous_scale=custom_color_scale,
                    range_color=[30, 85],
                    hover_data={'LAeq': True, 'number': True},
                    custom_data=['LAeq']
                    )

    fig.update_layout(title='Power Average Sound Pressure Level (LAeq)')
    fig.update_traces(hovertemplate='<b>%{label}</b><br>LAeq: %{customdata[0]:.2f} dB<br>Count: %{value}')
    fig.update_traces(texttemplate='%{label}<br><br>LAeq: %{customdata[0]:.2f} dB')

    fig.show()

    fig.write_html(f"{visualization_dir}/{title}_LAeq_Pred_{stable_version}.html")
    print(f"Saving image at {visualization_dir}/{title}_LAeq_Pred_{stable_version}.html")