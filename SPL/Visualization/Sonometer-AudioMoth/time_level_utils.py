import numpy as np
import pandas as pd

def calculate_duration(start_time, end_time):
    """Calculate duration in seconds
    Args:
        start_time: datetime with the start time
        end_time: datetime with the end time
    """
    duration = end_time - start_time
    return duration.total_seconds()

def evaluation_period_str(hour_column):
    """Label period based on hour columnn
    Args:
        hour_column: column name with the hour
    """
    period = ''
    if hour_column >= 7 and hour_column < 19:
        period = 'Ld'
    elif hour_column >= 19 and hour_column < 23:
        period = 'Le'
    else:
        period = 'Ln'
    return period

def evaluation_period_str_valencia(hour_column):
    """Label period based on hour columnn
    Args:
        hour_column: column name with the hour
    """
    period = ''
    if hour_column >= 8 and hour_column < 22:
        period = 'Ld_valencia'
    else:
        period = 'Ln_valencia'
    return period

def add_night_column(hour_column, day_col):
    """Add night column to Dataframe based on hour column and day column
    Args:
        hour_column: column name with the hour
        day_col: column name with the day
    """
    night_list=["Lunes-Martes","Martes-Miércoles","Miércoles-Jueves","Jueves-Viernes","Viernes-Sábado","Sábado-Domingo","Domingo-Lunes"]
    night = ''
    if hour_column >= 23:
        night=night_list[day_col]
    elif hour_column < 7:
        night=night_list[day_col-1]
    return night

def add_datetime_columns(df,date_col):
    """Add datetime Columns to Dataframe
    Args:
        df: pandas DataFrame with the measurement data
        date_col: column name with the datetime
    """
    #df['day_hour'] = df.apply(lambda x: str(x[date_col].day) + '-' + str(x[date_col].hour),axis=1)
    df['date'] = df[date_col].dt.date
    df['day'] = df[date_col].dt.day
    df['hour'] = df[date_col].dt.hour
    df['weekday'] = df[date_col].dt.weekday
    df['day_name'] = df[date_col].dt.day_name()
    
    #df['min_sec_str'] = df.apply(lambda x: datetime.datetime.strftime(x[date_col],'%M:%S'),axis=1)
    #df['min_sec_15_str'] = df.apply(lambda x: str(x[date_col].minute % 15) + '-'+str(x[date_col].second),axis=1)
    return df

def db_limit(hour_column,ld_limit,le_limit,ln_limit):
    """Create Columns on the Dataframe with Noise levels Limits on the measurement poiint
    Args:
        df: pandas DataFrame with the measurement data
        ld_limit: day limit
        le_limit: evening limit
        ln_limit: night limit
    """
    limit = 0
    if hour_column >= 7 and hour_column < 19:
        limit = ld_limit
    elif hour_column >= 19 and hour_column < 23:
        limit = le_limit
    else:
        limit = ln_limit
    return limit

def leq(levels):
    """Get the Leq from a list of levels
    Args:
        levels: list of levels
        
    Returns:
        leq: Leq
    """
    levels = levels[~np.isnan(levels)]
    l = np.array(levels)
    return 10*np.log10(np.mean(np.power(10,l/10)))

def get_day_levels(df,laeq_column):
    """Get the Leq for each day period
    Args:
        df: pandas DataFrame with the measurement data
        laeq_column: column name with the levels
    """
    df['indicador_str'] = df.apply(lambda x: evaluation_period_str(x['hour']),axis=1)
    indicadores = df.groupby('indicador_str').agg({laeq_column:[leq]}).round(1)
    return indicadores
    
def get_day_levels_valencia(df,laeq_column):
    """Get the Leq for each day period
    Args:
        df: pandas DataFrame with the measurement data
        laeq_column: column name with the levels
    """
    df['indicador_valencia'] = df.apply(lambda x: evaluation_period_str_valencia(x['hour']),axis=1)
    indicadores = df.groupby('indicador_valencia').agg({laeq_column:[leq]}).round(1)
    return indicadores


def remove_unnamed_columns(df_preds):
    df_preds = df_preds.loc[:, ~df_preds.columns.str.contains('^Unnamed')]
    df_preds = df_preds.drop(columns=['Brown_Level_1'])
    df_preds = df_preds.drop(columns=['index'])
    return df_preds

def yamnet_class_map_csv():
    yammnet_class_map = r"C:\Users\GIS2\Documents\santi\GitHub\AAC\AI_Model\Urban_Model\taxonomy_mapping\yamnet_class_AAC_v1_0.csv"
    df_audioset = pd.read_csv(yammnet_class_map,sep=';')
    df_audioset = remove_unnamed_columns(df_audioset)
    return df_audioset

def prediction_csv(path_input):
    df_prediction = pd.read_csv(path_input)
    df_prediction = df_prediction.drop(columns=['classes_custom'])
    return df_prediction