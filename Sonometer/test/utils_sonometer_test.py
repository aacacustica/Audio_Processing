from calendar import weekday
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
import numpy as np
from datetime import datetime
import os

######################## SLM COLUMN MAPS #####################################
larsonlx_dict = {'LAEQ_COLUMN': 'LAeq',
'LAMAX_COLUMN': 'LAFmax',
'LAMIN_COLUMN': 'LAFmin'}

larson824_dict = {'LAEQ_COLUMN': 'Leq',
'LAMAX_COLUMN': 'Max',
'LAMIN_COLUMN': 'Min'}

larson814_dict = {'LAEQ_COLUMN': 'Leq',
'LAMAX_COLUMN': 'Max',
'LAMIN_COLUMN': 'Min'}

cesva_dict = {'LAEQ_COLUMN': 'LA1s',
'LAMAX_COLUMN': 'LAFmax1s',
'LAMIN_COLUMN': 'LAFmin1s'}

SV307_dict = {'LAEQ_COLUMN': 'LAeq (Ch1, P1) [dB]',
'LAMAX_COLUMN': 'LAFmax (Ch1, P1) [dB]',
'LAMIN_COLUMN': 'LAFmin (Ch1, P1) [dB]' 
} 

audiopost_dict = {'LAEQ_COLUMN': 'LA',
'LAMAX_COLUMN': 'LAmax',
'LAMIN_COLUMN': 'LAmin'}

common_columns = ["datetime", "LAeq", "LAmax", "LAmin","ubicacion","slm_type"]

day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

######################## Funciones Lectura #####################################
def get_data_814(filename: str):
    try:
        df = pd.read_csv(filename, header=16, encoding='latin1')
    except UnicodeDecodeError:
        df = pd.read_csv(filename, header=16)
    if "Leq" not in df.columns:
        df = pd.read_csv(filename, header=19, sep=';', encoding='latin1')
    df['datetime'] = pd.to_datetime(df['Date'] + ' ' + df['Time'])
    return df

def get_data_lx_ES(filename: str):
    df = pd.read_excel(filename, sheet_name='Historia del tiempo')
    df['datetime'] = pd.to_datetime(df['Fecha'])
    return df

def get_data_824(filename: str):
    df = pd.read_csv(filename, sep=',', encoding='latin1', header=15)
    df = df.dropna(axis=1)
    # print(df)
    if "Leq" not in df.columns:
        df = pd.read_csv(filename,header=15, sep=',')
    df['datetime'] = pd.to_datetime(df['Date'] + ' '+ df['Time'])
    # print(df)
    return df

def get_data_SV307(filename: str):
    df = pd.read_csv(filename,header=14,skipfooter=8,usecols=[0,1,2,3,4,5,6,7,8], engine='python')
    if 'LAeq (Ch1, P1) [dB]' not in df.columns:
        df = pd.read_csv(filename,header=14,sep=';',skipfooter=8,usecols=[0,1,2,3,4,5,6,7,8], engine='python')
    df['datetime'] = pd.to_datetime(df['Time'],format="%d/%m/%Y %H:%M:%S")
    return df
    
def get_data_lx_EN(filename: str):
    df = pd.read_excel(filename,sheet_name=4)
    df['datetime'] = pd.to_datetime(df['Date'])
    return df

def get_data_audio(filename: str):
    df = pd.read_csv(filename)
    df['datetime'] = pd.to_datetime(df['date'])
    return df 

def get_data_cesva(measurement_folder: str):
    if os.path.isfile(measurement_folder):
        cesva_index = measurement_folder.find('CESVA')
        if cesva_index != -1:
            measurement_folder = measurement_folder[:cesva_index] + 'CESVA'
        else:
            raise ValueError("CESVA folder not found in the file path.")

    elif 'CESVA' not in measurement_folder:
        raise ValueError("The directory does not contain 'CESVA'.")
    
    cesva_files = []
    cols_to_use = ['Date hour','Elapsed t','LA1s','LAFmax1s','LAFmin1s']
    for root, dirs, files in os.walk(measurement_folder, topdown=False):
        for name in files:
            if name.endswith('.csv'):
                cesva_files.append(os.path.join(root, name))

    df_all = pd.DataFrame()
    for file_path in cesva_files:
        try:
            df = pd.read_csv(file_path,sep=';',header=11,decimal=',', usecols=cols_to_use)
            df.dropna(subset=['Elapsed t'],inplace=True) 
        except Exception as e: 
            pass
        try:
            df = pd.read_csv(file_path,sep=';',header=12,decimal=',',usecols=cols_to_use)
            df.dropna(subset=['Elapsed t'],inplace=True)   
        except Exception as e: 
            pass
        #df = df[['Date hour','Elapsed t','LA1s','LAFmax1s','LAFmin1s']]
        df_all = pd.concat([df_all,df])
    df = df_all.copy()
    del df_all
    for col in df.columns:
        if col not in  ["Date hour", "Elapsed t"]:
            df[col] = pd.to_numeric(df[col])
    
    df['datetime'] = df.apply(lambda x: datetime.strptime(x['Date hour'], '%d/%m/%Y %H:%M:%S'),axis=1)
    df['datetime'] = pd.to_datetime(df['datetime'])
    return df

#----------------------------------------------------------------------------------
def evaluation_period_str(hour_column):
    ''' Label period based on hour columnn'''
    period = ''

    if hour_column >= 7 and hour_column < 19:
        period = 'Ld'

    elif hour_column >= 19 and hour_column < 23:
        period = 'Le'

    else:
        period = 'Ln'
    return period

def evaluation_period_str_valencia(hour_column):
    ''' Label period based on hour columnn'''
    period = ''

    if hour_column >= 8 and hour_column < 22:
        period = 'Ld_valencia'

    else:
        period = 'Ln_valencia'
    return period

def add_night_column(hour_column, day_col):
    ''' Label based on hour columnn and weekday'''

    night_list=["Lunes-Martes","Martes-Miércoles","Miércoles-Jueves","Jueves-Viernes","Viernes-Sábado","Sábado-Domingo","Domingo-Lunes"]
    night = ''
 
    if hour_column >= 23:
        night=night_list[day_col]

    elif hour_column < 7:
        night=night_list[day_col-1]

    return night

def add_datetime_columns(df,date_col):
    """Add datetime Columns to Dataframe"""
    
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
    """Create Columns on the Dataframe with Noise levels Limits on the measurement poiint"""
    
    limit = 0
    if hour_column >= 7 and hour_column < 19:
        limit = ld_limit
    elif hour_column >= 19 and hour_column < 23:
        limit = le_limit
    else:
        limit = ln_limit
    return limit

def leq(levels):
    levels = levels[~np.isnan(levels)]
    l = np.array(levels)
    return 10*np.log10(np.mean(np.power(10,l/10)))

def get_day_levels(df,laeq_column):
    df['indicador_str'] = df.apply(lambda x: evaluation_period_str(x['hour']),axis=1)
    indicadores = df.groupby('indicador_str').agg({laeq_column:[leq]}).round(1)
    return indicadores
    
def get_day_levels_valencia(df,laeq_column):
    df['indicador_valencia'] = df.apply(lambda x: evaluation_period_str_valencia(x['hour']),axis=1)
    indicadores = df.groupby('indicador_valencia').agg({laeq_column:[leq]}).round(1)
    return indicadores

#-----------------------------------------------------------------------------------------

# color scale

cmap_dict = sns.color_palette(palette=["#C8FFC8", "#00C800", "#007800", "#FFFF00", "#FFC878", "#FF9600", "#FF0000", "#780000", "#FF00FF", "#8C3CFF", "#000078"],n_colors=11)
    

def plot_day_evolution(df, laeq_column:str, plotname:str):
    """ Lineplots for each day """


    fig = sns.relplot(data=df,
                      x="hour",
                      y=laeq_column,
                      kind="line",
                      hue="day_name",
                      estimator=leq,
                      aspect=1.3,
                      ) 
    (fig.map(plt.axvline, x=7, color=".7", dashes=(2, 1), zorder=0))
    (fig.map(plt.axvline, x=19, color=".7", dashes=(2, 1), zorder=0))
    (fig.map(plt.axvline, x=23, color=".7", dashes=(2, 1), zorder=0))


    (fig.map(plt.text, s="Ln", x=0.1, y= 0.9,transform=plt.gca().transAxes, c="Black"))
    (fig.map(plt.text, s="Ld", x=0.35, y= 0.9,transform=plt.gca().transAxes, c="Black"))
    (fig.map(plt.text, s="Le", x=0.82, y= 0.9,transform=plt.gca().transAxes, c="Black"))

    
    plt.ylabel('dB(A)')
    plt.xlabel('Hora')
    fig.savefig(f"{plotname}_day_evolution.png",dpi=150)
    plt.close()

def plot_period_evolution(df, laeq_column:str, plotname:str):
    """ Lineplots per each period """

    for ind in df["indicador_str"].unique():
        df_temp = df[df["indicador_str"] == ind]

        fig = sns.relplot(data=df_temp,
                          x="hour",
                          y=laeq_column,
                          kind="line",
                          hue="day_name",
                          estimator=leq,
                          )
        if ind == "Ln":
            plt.xlim(0, 6)

        plt.title(ind)
        plt.ylabel('dB(A)')
        plt.xlabel('Hora')
        fig.savefig(f"{plotname}_{ind}period_evolution.png",dpi=150)
        plt.close()

def plot_night_evolution(df, laeq_column:str, plotname:str):

    df_temp = df[df["indicador_str"] == 'Ln']
    print(df_temp)

    fig = sns.relplot(data=df_temp,
                        x="hour",
                        y=laeq_column,
                        kind="line",
                        style="night_str",
                        estimator=leq,
                        )

    plt.title('Evolución noche')
    plt.ylabel('dB(A)')
    plt.xlabel('Hora')
    fig.savefig(f"{plotname}_night_evolution.png",dpi=150)
    plt.close()

def plot_heatmap(df,values_column: str, agg_func: str, plotname:str):
    """Plot heatmap of pivot table with hour evolution of each day,

    Args:
        df (_type_): DataFrame
        values_column (str): Name of the column to use, tipycally LAeq
        agg_func (str): Aggregation function, Leq
        plotname (str): Prefix to name the plot
    """
       
    # pivot table and then heatmap
    leq_day_hour = pd.pivot_table(df, values=values_column, index=['date'],columns=['hour'], aggfunc=agg_func).round(1)
    plt.figure(figsize=(20,5))
    sns.heatmap(leq_day_hour, vmin=30, vmax= 85, cmap=cmap_dict, annot=True)
    # fix for mpl bug that cuts off top/bottom of seaborn viz
    # b, t = plt.ylim() # discover the values for bottom and top
    # b += 0.5 # Add 0.5 to the bottom
    # t -= 0.5 # Subtract 0.5 from the top
    # plt.ylim(b, t) # update the ylim(bottom, top) values
    plt.xlabel('Hora')
    plt.ylabel('Día')
    plt.tight_layout()
    plt.savefig(f'{plotname}_heatmap.png',dpi=150)
    #leq_day_hour.to_csv(f"{file[:-4]}_heatmap_mes_tabla_{month}_{year}.csv")
    leq_day_hour.to_excel(f'{plotname}_hetmap_tabla_dia_hora.xlsx')
    plt.close()
    
def make_timeplot(df, columns_dict: dict, agg_period: int, plotname: str, percentiles: bool):
    
    """ Plot Indicator time evolution in the measurument period """
    
    leq_agg = df.resample(f'{agg_period}s').agg({columns_dict['LAEQ_COLUMN']: [leq]})
    lmax = df.resample(f'{agg_period}s').agg({columns_dict['LAMAX_COLUMN']: 'max'})
    lmin = df.resample(f'{agg_period}s').agg({columns_dict['LAMIN_COLUMN']: 'min'})
    #oca = df.resample(f'{agg_period}s').agg({'oca': 'min'})

    L90 = df[columns_dict['LAEQ_COLUMN']].resample(f'{agg_period}s').quantile(0.1)
    L50 = df[columns_dict['LAEQ_COLUMN']].resample(f'{agg_period}s').quantile(0.5)
    L10 = df[columns_dict['LAEQ_COLUMN']].resample(f'{agg_period}s').quantile(0.9)
    L5 = df[columns_dict['LAEQ_COLUMN']].resample(f'{agg_period}s').quantile(0.95)
    L1 = df[columns_dict['LAEQ_COLUMN']].resample(f'{agg_period}s').quantile(0.99)


    hours = mdates.HourLocator(interval = 2)
    fig, ax = plt.subplots(figsize=(20,10))
    ax.set_facecolor("white")

    x = leq_agg.index
    ax.plot(x, leq_agg.values,linewidth=3, color='red')
    ax.plot(x, lmax.values,linewidth=1, color='#FF99FF')
    ax.plot(x, lmin.values,linewidth=1, color='#92D050')
    # OCA
    # #ax.plot(x, oca.values, color='#00B0F0')

    if percentiles:
        ax.plot(x,L90,linewidth=0.5, color='#9E9E9E')
        ax.plot(x,L50,linewidth=0.5, color='#FFABAB')
        ax.plot(x,L10,linewidth=0.5, color='#B2E2F2')
        ax.plot(x,L5,linewidth=0.5, color='#6EB5FF')
        ax.plot(x,L1,linewidth=0.5, color='#B28DFF')
    
    
    ax.xaxis.set_major_locator(hours)
    h_fmt = mdates.DateFormatter('%H:%M')
    ax.xaxis.set_major_formatter(h_fmt)
    
    #plt.title(f'{plotname} Nivel equivalente {agg_period}s')
    plt.ylabel('dB(A)')
    plt.xlabel('Hora')
    plt.xticks(rotation=45)
    plt.ylim([30,105])
    #plt.grid()
    plt.legend(['LAeq','Lmax','Lmin','L90','L50','L10','L5','L1'],bbox_to_anchor=(1.1, 1.05))
     

    plt.tight_layout()
    plt.savefig(f'{plotname}_{agg_period}s_timeplot.png',dpi=150)
    plt.close()

def plot_indheatmap(df, plotname:str, ind_column:str):
    
    indicadores_table = pd.pivot_table(data=df,index="date",columns="indicador_str",values=ind_column,aggfunc=leq).round(1)
    print(indicadores_table)
    sns.heatmap(indicadores_table, annot=True,fmt=".1f",linewidth=0.5, cmap=cmap_dict,vmin=30,vmax=85)
    
    indicadores_table.to_excel(f"{plotname}_indicadores.xlsx")
    
    plt.ylabel('Día')
    plt.xlabel('Indicador')
    plt.savefig(f"{plotname}_indicadores.png")
    plt.close()
