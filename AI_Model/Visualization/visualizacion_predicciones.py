import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from matplotlib.colors import ListedColormap
import ast
import numpy as np
import os

MIN_5 = 320
MIN_10 = 620
MIN_15 = 1000
MIN_30 = 1820
MIN_60 = 3620
MIN_120 = 7220

def extract_location(file_path):
    file_name = os.path.basename(file_path)
    
    if "TENERIFE" in file_name and "FREEOLSEN" in file_name:
        return "Tenerife, Fred Olsen"
    elif "TENERIFE" in file_name and "ARMAS" in file_name:
        return "Tenerife, Armas"
    elif "espolon" in file_name and "petronor" in file_name:
        return "Espolón Petronor"
    else:
        return "Unknown Location"

def remove_label(classes_list, label):
    return [x for x in classes_list if x != label]

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
    df["year"] = df.index.year
    df["month"] = df.index.month
    df["day"] = df.index.day
    df["hour"] = df.index.hour
    df["minute"] = df.index.minute
    df["second"] = df.index.second
    df["weekday"] = df.index.day_name()

    weekday_translation = {
        "Monday": "Lunes",
        "Tuesday": "Martes",
        "Wednesday": "Miércoles",
        "Thursday": "Jueves",
        "Friday": "Viernes",
        "Saturday": "Sábado",
        "Sunday": "Domingo"
    }
    df["weekday"] = df["weekday"].replace(weekday_translation)
    df["weekday"] = df["weekday"].astype(str)
    df["day"] = df["day"].astype(str).str.zfill(2)
    df["fullday"] = df["day"] + "," + df["weekday"]

    return df

# tenerife_fred_olsen = "csv/avg_predictions_original_custom_10p_TENERIFE_FREEOLSEN.csv"
# tenerife_la_palma = "avg_predictions_original_custom_10p_LA_PALMA_ARMAS.csv"
espolon_petronor = "/home/aaccolombia/Documents/AAC/NoisePort/Noiseport/Audio_Processing/Test/yamnet_programs/results_20221026/10-probs/avg_predictions_original_custom_10espolon_petronor-20221006.csv"
torreta_petronor = "csv/avg_predictions_original_custom_10p_torreta_petronor-20221027.csv"

# df = pd.read_csv(tenerife_fred_olsen, sep=";")
# df = pd.read_csv("avg_predictions_original_custom_10p_LA_PALMA_ARMAS.csv")
# df = pd.read_csv(espolon_petronor)
df = pd.read_csv(torreta_petronor)

title = extract_location(espolon_petronor)

df

print("We are working with {} processing results".format(len(df)))
print(f"We are working within the time range from [ {df['datetime'].min()} ] to [ {df['datetime'].max()} ]")

df['datetime'] = pd.to_datetime(df['datetime'])
time_difference_seconds = df['datetime'].diff().dt.total_seconds()
average_interval = time_difference_seconds.mean()
interval_printing(average_interval)

# convert string to list
df['classes_custom'] = df['classes_custom'].apply(ast.literal_eval)

print(f"Type of the column: \t\t {type(df['classes_custom'])}")
print(f"Type of the first element: \t\t {type(df['classes_custom'][0])}")

# df['classes_custom'] = df['classes_custom'].apply(lambda x: remove_label(x, 'Nature'))
# df['classes_custom'] = df['classes_custom'].apply(lambda x: remove_label(x, 'Voice'))

df['classes_custom']

# print("Nature" in df['classes_custom'])
# print("Voice" in df['classes_custom'])

df['classes_custom'] = df['classes_custom'].apply(first_element)
df['classes_custom']

print(f"These are the class count:\n\n{df['classes_custom'].value_counts()}")

print(f"\nThese are the class summed: \t\t {df['classes_custom'].value_counts().sum()}")
print(f"This is the lenght of the dataframe \t {len(df)}")

df['single_class'] = df['classes_custom'].apply(lambda x: x[0] if x else None)
df.set_index("datetime", inplace=True)
df = insert_dates(df)

df

df = df.sort_values(by=["year", "month", "fullday"])

class_to_num = {class_name: index+1 for index, class_name in enumerate(df['single_class'].unique())}
df['class_num'] = df['single_class'].map(class_to_num)

clase_nombres = {v: k for k, v in class_to_num.items()}

legend_colors = sns.color_palette("husl", n_colors=len(clase_nombres))
cmap = sns.color_palette(legend_colors, n_colors=len(clase_nombres))
legend_elements = [Patch(facecolor=color, label=f"Clase {cls_num} - {clase_nombres.get(cls_num, '')}") for cls_num, color in zip(clase_nombres.keys(), cmap)]

plt.figure(figsize=(18, 10))

day_class = pd.pivot_table(data=df, columns=df.index.time, index=["year", "month", "fullday"], values="class_num", aggfunc='mean')

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

plt.show()

day = "29"

# Filter for the specific day across all years and months
df_xth = df[df["fullday"].str.startswith(day)]

if df_xth.empty:
    print(f"No data for the {day}th day across all years and months. Skipping...")
else:
    plt.figure(figsize=(20, 10))
    
    # Pivot with year and month as multi-index
    day_class = pd.pivot_table(data=df_xth, columns=df_xth.index.time, index=["year", "month"], values="class_num", aggfunc=lambda x: x.mode()[0] if not x.empty else None)
    
    if day_class.isna().all().all() or day_class.empty:
        print(f"No valid data for the {day}th day. Skipping...")
    else:
        unique_classes = day_class.dropna().values.flatten()
        unique_classes = set(unique_classes)
        
        current_legend_elements = [Patch(facecolor=cmap[int(cls_num)-1], label=f"Clase {cls_num} - {clase_nombres[cls_num]}") for cls_num in unique_classes]
        ax = sns.heatmap(day_class, annot=False, cmap=cmap, linewidth=0.5, cbar=False, vmin=1, vmax=len(clase_nombres))
        ax.set_xticklabels(ax.get_xticklabels(), rotation=90)
        
        # Remove the y-tick labels (to hide year and month labels on y-axis)
        ax.yaxis.set_visible(False)
        
        # Update title to include year, month, and day
        years = "-".join(map(str, df_xth["year"].unique()))
        months = "-".join(map(str, sorted(df_xth["month"].unique())))
        plt.legend(handles=current_legend_elements, title="Clases", loc='center left', bbox_to_anchor=(1, 0.5))
        plt.title(f"{title} | Data for {years}-{months}-{day}")

        plt.show()

day = "29"

for year in sorted(df["year"].unique()):
    df_year = df[df["year"] == year]
    for month in sorted(df_year["month"].unique()):
        df_temp = df_year[df_year["month"] == month]
        
        df_xth = df_temp[df_temp["fullday"].str.startswith(day)]
        
        start_time = pd.to_datetime("13:18:00").time()
        end_time = pd.to_datetime("16:04:00").time()
        time_mask = (df_xth.index.time >= start_time) & (df_xth.index.time <= end_time)
        df_xth_filtered = df_xth[time_mask]
        
        if df_xth_filtered.empty:
            print(f"No data for the {day}th day in Year: {year}, Month: {month} within the specified time range. Skipping...")
            continue
        
        plt.figure(figsize=(18, 10))
        
        day_class = pd.pivot_table(data=df_xth_filtered, columns=df_xth_filtered.index.time, index="fullday", values="class_num", aggfunc=lambda x: x.mode()[0] if not x.empty else None)
        
        if day_class.isna().all().all() or day_class.empty:
            print(f"No valid data for Year: {year}, Month: {month}, Day: {day} within the specified time range. Skipping...")
            continue
        
        unique_classes = day_class.dropna().values.flatten()
        unique_classes = set(unique_classes)
        
        current_legend_elements = [Patch(facecolor=cmap[int(cls_num)-1], label=f"Clase {cls_num} - {clase_nombres[cls_num]}") for cls_num in unique_classes]
        ax = sns.heatmap(day_class, annot=False, cmap=cmap, linewidth=0.5, cbar=False, vmin=1, vmax=len(clase_nombres))
        ax.set_xticklabels(ax.get_xticklabels(), rotation=0)
        
        # Completely hide the y-axis
        ax.yaxis.set_visible(False)
        
        plt.legend(handles=current_legend_elements, title="Clases", loc='center left', bbox_to_anchor=(1, 0.5))
        plt.title(f"{title} | Data for {year}-{month}-{day} within {start_time} to {end_time}")

        plt.show()



