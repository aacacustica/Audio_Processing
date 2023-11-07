import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import os
import plotly.io as pio
pio.renderers.default='notebook'
import plotly.express as px
import datetime
import ast


START_TIME_SPECIFIC = "2022-10-29 13:00:00"
END_TIME_SPECIFIC = "2022-10-29 15:15:00"

def extract_location(file_path):
    file_name = os.path.basename(file_path)
    if "TENERIFE" in file_name and "FREEOLSEN" in file_name:
        return "Tenerife, Fred Olsen"
    elif "TENERIFE" in file_name and "ARMAS" in file_name:
        return "Tenerife, Armas"
    elif "espolon" in file_name and "petronor" in file_name:
        return "Espolón Petronor"
    elif "torreta" in file_name:
        return "Torreta Petronor"
    else:
        return "Unknown Location"
    
def postprocessing_df(df_preds):
    df_preds.drop(columns=['classes_custom', 'probabilities_custom', 'sum_probs_custom', 'sum_probs_original'],inplace=True)
    df_preds.rename(columns={'datetime':'filenames', 'classes_original':'classes'}, inplace=True)
    df_preds['classes'] = df_preds['classes'].apply(ast.literal_eval)
    
    return df_preds

def insert_time(df_preds):
    df_preds['date'] = pd.to_datetime(df_preds['filenames'])

    df_preds['year'] = df_preds.apply(lambda x: x['date'].year, axis= 1)
    df_preds['month'] = df_preds.apply(lambda x: x['date'].month, axis= 1)
    df_preds['day'] = df_preds.apply(lambda x: x['date'].day, axis= 1)

    df_preds['day_name'] = df_preds.apply(lambda x: x['date'].day_name(), axis= 1)
    df_preds['weekday'] = df_preds.apply(lambda x: x['date'].weekday(), axis= 1)
    
    df_preds['hour'] = df_preds.apply(lambda x: x['date'].hour, axis= 1)
    df_preds['hour_min'] = df_preds.apply(lambda x: str(x['date'].hour) + '_' + str(x['date'].minute),axis=1)
    
    df_preds['time'] = df_preds.apply(lambda x: x['date'].time(),axis=1)
    
    return df_preds

def index_and_explode(df):
    df.set_index('time',inplace=True)
    df = df.explode('classes')
    df['display_name'] = df['classes']
    df['number'] = 1
    
    return df

def merge_dataframes(df, union):
    df = df.merge(union,how='left',on='display_name')
    
    return df

def remove_label(df, column, label):
    df_no_label = df[df[column] != label]
    return df_no_label, label

# sort by time column called datetime
def sort_df(df):
    df.sort_values(by=['datetime'], inplace=True)
    return df


# df_preds = pd.read_csv(f'avg_predictions_{abrev}.csv', converters={'classes': eval})
yammnet_class_map = 'yamnet_class_map_rev_FINAL.csv'
union = pd.read_csv(yammnet_class_map,sep=';')

# tenerife_fred_olsen = "csv/avg_predictions_original_custom_10p_TENERIFE_FREEOLSEN.csv"
# tenerife_la_palma = "avg_predictions_original_custom_10p_LA_PALMA_ARMAS.csv"
# espolon_petronor = "/home/aaccolombia/Documents/AAC/NoisePort/Noiseport/Audio_Processing/Test/yamnet_programs/results_20221026/10-probs/avg_predictions_original_custom_10espolon_petronor-20221006.csv"
torreta_petronor = "csv/avg_predictions_original_custom_10p_torreta_petronor-20221027.csv"

# df = pd.read_csv(tenerife_fred_olsen, sep=";")
# df = pd.read_csv("avg_predictions_original_custom_10p_LA_PALMA_ARMAS.csv")
df_preds = pd.read_csv(torreta_petronor)
# df_preds = pd.read_csv(espolon_petronor)

title = extract_location(torreta_petronor)

df_preds

df_preds = sort_df(df_preds)
df_preds = postprocessing_df(df_preds)
df_preds = insert_time(df_preds)

df = df_preds.copy()

df = index_and_explode(df)
df = merge_dataframes(df, union)


start_date = df.sort_values('date')['date'].iloc[0]
end_date = df.sort_values('date')['date'].iloc[-1]
print('Inicio Monitoreo: {} Final Monitoreo: {}'.format(start_date,end_date))

unique_classes = set(df['classes'].unique())
df_no_Nature, label = remove_label(df, 'Brown_Level_2', 'Nature')


# **PLOTTING GLOBAL DASH BOARD**
fig = px.treemap(df, 
                    path=['Brown_Level_2', 'classes'], 
                    values='number'
                )
fig.update_layout(title=f'{title} Global | From {df["date"].iloc[0]}  to {df["date"].iloc[-1]}')
fig.show()

fig = px.treemap(df_no_Nature, 
                    path=['Brown_Level_2', 'classes'], 
                    values='number'
                )
fig.update_layout(title=f'{title} Global Sin {label} | {df["date"].iloc[0]} - {df["date"].iloc[-1]}')
fig.show()


# **PLOTTING EACH DAY**
for day in df['day'].unique():
    day_df = df[df['day'] == day]
    fig = px.treemap(day_df, 
                     path=['Brown_Level_2', 'classes'], 
                     values='number'
                    )
    fig.update_layout(title=f'{title} | {day_df["year"].iloc[0]}-{day_df["month"].iloc[0]}-{day}')

    fig.show()

for day in df_no_Nature['day'].unique():
    day_df = df_no_Nature[df_no_Nature['day'] == day]
    fig = px.treemap(df_no_Nature, 
                     path=['Brown_Level_2', 'classes'], 
                     values='number'
                    )
    fig.update_layout(title=f'{title} Sin {label} | {day_df["year"].iloc[0]}-{day_df["month"].iloc[0]}-{day}')

    fig.show()

# **PLOTTING SPECIFIC TIME SPANS**
start_time = pd.Timestamp(START_TIME_SPECIFIC)
end_time = pd.Timestamp(END_TIME_SPECIFIC)

filtered_df = df[(df['date'] >= start_time) & (df['date'] <= end_time)]

filtered_df['number'] = 1
fig = px.treemap(filtered_df, 
                    path=['Brown_Level_2', 'classes'], 
                    values='number'
                )
fig.update_layout(title=f'{title} | {start_time} - {end_time} ')
fig.show()

start_time = pd.Timestamp(START_TIME_SPECIFIC)
end_time = pd.Timestamp(END_TIME_SPECIFIC)
filtered_df = df_no_Nature[(df['date'] >= start_time) & (df['date'] <= end_time)]

filtered_df['number'] = 1
fig = px.treemap(filtered_df, 
                    path=['Brown_Level_2', 'classes'], 
                    values='number'
                )
fig.update_layout(title=f'{title} Sin {label} | {start_time} - {end_time} ')
fig.show()

start_time = pd.Timestamp("2022-10-29 20:00:00")
end_time = pd.Timestamp("2022-10-29 21:00:00")
filtered_two_df = df[(df['date'] >= start_time) & (df['date'] <= end_time)]

filtered_df = df[(df['date'] >= start_time) & (df['date'] <= end_time)]

filtered_df['number'] = 1
fig = px.treemap(filtered_df, 
                    path=['Brown_Level_2', 'classes'], 
                    values='number'
                )
fig.update_layout(title=f'{title} | {start_time} - {end_time} ')
fig.show()

start_time = pd.Timestamp("2022-10-20 13:30:00")
end_time = pd.Timestamp("2022-10-20 14:50:00")
filtered_two_df = df_no_Nature[(df['date'] >= start_time) & (df['date'] <= end_time)]

filtered_two_df['number'] = 1
fig = px.treemap(filtered_two_df, 
                    path=['Brown_Level_2', 'classes'], 
                    values='number'
                )
fig.update_layout(title=f'{title} Sin {label} | {start_time} - {end_time}')
fig.show()

start_time = pd.Timestamp("2022-10-29 21:20:00")
end_time = pd.Timestamp("2022-10-29 23:55:00")
filtered_df = df[(df['date'] >= start_time) & (df['date'] <= end_time)]

filtered_df['number'] = 1
fig = px.treemap(filtered_df, 
                    path=['Brown_Level_2', 'classes'], 
                    values='number'
                )
fig.update_layout(title=f'{title} | {start_time} - {end_time} ')
fig.show()

start_time = pd.Timestamp("2022-11-09 09:45:00")
end_time = pd.Timestamp("2022-11-09 12:00:00")
filtered_df = df[(df['date'] >= start_time) & (df['date'] <= end_time)]

filtered_df['number'] = 1
fig = px.treemap(filtered_df, 
                    path=['Brown_Level_2', 'classes'], 
                    values='number'
                )
fig.update_layout(title=f'{title} | {start_time} - {end_time} ')
fig.show()

start_time = pd.Timestamp("2022-11-14 11:00:00")
end_time = pd.Timestamp("2022-11-14 13:00:00")
filtered_df = df[(df['date'] >= start_time) & (df['date'] <= end_time)]

filtered_df['number'] = 1
fig = px.treemap(filtered_df, 
                    path=['Brown_Level_2', 'classes'], 
                    values='number'
                )
fig.update_layout(title=f'{title} | {start_time} - {end_time} ')
fig.show()

