import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
from utils_plotter import *
import os

cmap_dict = sns.color_palette(palette=["#C8FFC8", "#00C800", "#007800", "#FFFF00", "#FFC878", "#FF9600", "#FF0000", "#780000", "#FF00FF", "#8C3CFF", "#000078"],n_colors=11)
    
def plot_day_evolution(df, folder_output_dir: str, logger, laeq_column:str, plotname:str):
    """ Lineplots for each day
    Args:
        df (_type_): DataFrame
        folder_output_dir (str): Output directory
        logger (_type_): Logger
        laeq_column (str): Name of the column to use, tipycally LAeq
        plotname (str): Prefix to name the plot
    """
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
    plt.title(f'Evolución día {plotname}')
   
    os.makedirs(f'{folder_output_dir}', exist_ok=True)
    fig.savefig(f"{folder_output_dir}/{plotname}_day_evolution.png",dpi=150)
    df.to_excel(f"{folder_output_dir}/{plotname}_day_evolution.xlsx")
   
    plt.close()
   
    logger.info(f"Day evolution plot saved to {folder_output_dir}/{plotname}_day_evolution.png")
    logger.info(f"Day evolution data saved to {folder_output_dir}/{plotname}_day_evolution.xlsx")

def plot_period_evolution(df,  folder_output_dir: str, logger, laeq_column:str, plotname:str):
    """ Lineplots per each period
    Args:
        df (_type_): DataFrame
        folder_output_dir (str): Output directory
        logger (_type_): Logger
        laeq_column (str): Name of the column to use, tipycally LAeq
        plotname (str): Prefix to name the plot
    """
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

        plt.title(f"Evolución {ind}")
        plt.ylabel('dB(A)')
        plt.xlabel('Hora')
       
        os.makedirs(f'{folder_output_dir}', exist_ok=True)
        fig.savefig(f"{folder_output_dir}/{plotname}_{ind}_evolution.png",dpi=150)
        df_temp.to_excel(f"{folder_output_dir}/{plotname}_{ind}_evolution.xlsx")
       
        plt.close()
    
    logger.info(f"Period evolution plot saved to {folder_output_dir}/{plotname}_{ind}_evolution.png")
    logger.info(f"Period evolution data saved to {folder_output_dir}/{plotname}_{ind}_evolution.xlsx")

def plot_night_evolution(df, folder_output_dir: str, logger, laeq_column:str, plotname:str):
    """ Lineplots per each night
    Args:
        df (_type_): DataFrame
        folder_output_dir (str): Output directory
        logger (_type_): Logger
        laeq_column (str): Name of the column to use, tipycally LAeq
        plotname (str): Prefix to name the plot
    """
    df_temp = df[df["indicador_str"] == 'Ln']

    fig = sns.relplot(data=df_temp,
                        x="hour",
                        y=laeq_column,
                        kind="line",
                        style="night_str",
                        estimator=leq,
                        )

    plt.title(f'Evolución noche {plotname}')
    plt.ylabel('dB(A)')
    plt.xlabel('Hora')
    
    os.makedirs(f'{folder_output_dir}', exist_ok=True)
    fig.savefig(f"{folder_output_dir}/{plotname}_night_evolution.png",dpi=150)
    df_temp.to_excel(f"{folder_output_dir}/{plotname}_night_evolution.xlsx")
    
    plt.close()
    
    logger.info(f"Night evolution plot saved to {folder_output_dir}/{plotname}_night_evolution.png")
    logger.info(f"Night evolution data saved to {folder_output_dir}/{plotname}_night_evolution.xlsx")

def plot_heatmap(df, folder_output_dir: str, logger, values_column: str, agg_func: str, plotname:str):
    """Plot heatmap of pivot table with hour evolution of each day,
    Args:
        df (_type_): DataFrame
        folder_output_dir (str): Output directory
        logger (_type_): Logger
        values_column (str): Name of the column to use, tipycally LAeq
        agg_func (str): Aggregation function, Leq
        plotname (str): Prefix to name the plot
    """
    try:
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
        plt.title(f'{plotname} Nivel equivalente')
        plt.tight_layout()
        
        os.makedirs(f'{folder_output_dir}', exist_ok=True)
        plt.savefig(f'{folder_output_dir}/{plotname}_heatmap.png',dpi=150)
        #leq_day_hour.to_csv(f"{file[:-4]}_heatmap_mes_tabla_{month}_{year}.csv")
        leq_day_hour.to_excel(f'{folder_output_dir}/{plotname}_heatmap_tabla_dia_hora.xlsx')
        
        plt.close()
        
        logger.info(f"Heatmap plot saved to {folder_output_dir}/{plotname}_heatmap.png")
        logger.info(f"Heatmap data saved to {folder_output_dir}/{plotname}_heatmap_tabla_dia_hora.xlsx")
    except Exception as e:
        logger.error(f"Error in plot_heatmap: {e}")
        
def make_timeplot(df: pd.DataFrame, folder_output_dir: str, logger, columns_dict: dict, agg_period: int, plotname: str, percentiles: list):
    """
    Plot Indicator time evolution in the measurement period.

    Args:
        df (pd.DataFrame): DataFrame containing the data.
        folder_output_dir (str): Output directory.
        logger: Logger for logging messages.
        columns_dict (dict): Dictionary with the column names.
        agg_period (int): Aggregation period in seconds.
        plotname (str): Prefix to name the plot.
        percentiles (list): List of percentiles to plot.
    """
    try:
        agg_funcs = {
            columns_dict['LAEQ_COLUMN']: 'mean',
            columns_dict['LAMAX_COLUMN']: 'max',
            columns_dict['LAMIN_COLUMN']: 'min'
        }
        agg_data = df.resample(f'{agg_period}s').agg(agg_funcs)

        percentiles_dict = {
            f'L{percentile}': df[columns_dict['LAEQ_COLUMN']].resample(f'{agg_period}s').quantile(percentile/100)
            for percentile in percentiles
        }

        plt.style.use('seaborn-whitegrid')
        fig, ax = plt.subplots(figsize=(20, 10))
        ax.set_facecolor("white")

        x = agg_data.index
        ax.plot(x, agg_data[columns_dict['LAEQ_COLUMN']], linewidth=3, color='red', label='LAeq')
        ax.plot(x, agg_data[columns_dict['LAMAX_COLUMN']], linewidth=1, color='#FF99FF', label='Lmax')
        ax.plot(x, agg_data[columns_dict['LAMIN_COLUMN']], linewidth=1, color='#92D050', label='Lmin')

        for percentile_value in percentiles:
            values = percentiles_dict[f'L{percentile_value}']
            ax.plot(x, values, linewidth=0.5, label=f'L{int(percentile_value)}')

        hours = mdates.HourLocator(interval=3)
        h_fmt = mdates.DateFormatter('%d-%m-%y %H:%M')
        
        ax.xaxis.set_major_locator(hours)
        ax.xaxis.set_major_formatter(h_fmt)
        
        plt.xlim(df.index.min(), df.index.max())
        plt.ylim([30, 105])
        plt.ylabel('dB(A)')
        plt.xlabel('Hora')
        
        plt.title(f'{plotname} Nivel equivalente {agg_period}s')
        
        plt.xticks(rotation=90)
        plt.legend(loc='upper left', bbox_to_anchor=(1.02, 1), borderaxespad=0.1, fancybox=True, framealpha=1, edgecolor='black')

        os.makedirs(folder_output_dir, exist_ok=True)
        plt.savefig(f'{folder_output_dir}/{plotname}_{agg_period}s_timeplot.png', dpi=150)
        agg_data.to_excel(f'{folder_output_dir}/{plotname}_{agg_period}s_timeplot.xlsx')

        plt.close()

        logger.info(f"Timeplot saved to {folder_output_dir}/{plotname}_{agg_period}s_timeplot.png")
        logger.info(f"Timeplot data saved to {folder_output_dir}/{plotname}_{agg_period}s_timeplot.xlsx")
    except Exception as e:
        logger.error(f"Error in make_timeplot: {e}")

def plot_indheatmap(df, folder_output_dir: str, logger, plotname:str, ind_column:str):
    """Plot heatmap of pivot table with hour evolution of each day
    Args:
        df (_type_): DataFrame
        folder_output_dir (str): Output directory
        logger (_type_): Logger
        plotname (str): Prefix to name the plot
        ind_column (str): Name of the column to use, tipycally LAeq
    """
    try:
        # Ld>21600
        # Le>7200
        # Ln>14400

        # print(df.columns)
        
        #     Index(['Registro #', 'Tipo de registro', 'Fecha', 'Hora', 'LAeq', 'LAFmax',
        #    'LAFmin', 'OVLD', 'Marcador', 'Comments', 'date', 'day', 'hour',
        #    'weekday', 'day_name', 'indicador_str'],
        #     dtype='object')
    
        print(df.head())
        
        # get the first and last date for each indicador
        indicadores = df.groupby('indicador_str').agg({'date':['min','max']})
        print(indicadores)
        exit()
        
        indicadores_table = pd.pivot_table(data=df,index="date",columns="indicador_str",values=ind_column,aggfunc=leq).round(1)
        sns.heatmap(indicadores_table, annot=True,fmt=".1f",linewidth=0.5, cmap=cmap_dict,vmin=30,vmax=85)
        
        plt.ylabel('Día')
        plt.xlabel('Indicador')
        plt.title(f'{plotname} Indicadores')
        
        os.makedirs(f'{folder_output_dir}', exist_ok=True)
        plt.savefig(f"{folder_output_dir}/{plotname}_indicadores.png")
        indicadores_table.to_excel(f"{folder_output_dir}/{plotname}_indicadores.xlsx")
        
        plt.close()
        
        logger.info(f"Indicadores data saved to {folder_output_dir}/{plotname}_indicadores.xlsx")
        logger.info(f"Indicadores plot saved to {folder_output_dir}/{plotname}_indicadores.png")
    
    except Exception as e:
        logger.error(f"Error in plot_indheatmap: {e}")