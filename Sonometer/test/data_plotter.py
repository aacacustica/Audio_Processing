import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
from utils_plotter import *
import os
from config import *

cmap_dict = sns.color_palette(palette=["#C8FFC8", "#00C800", "#007800", "#FFFF00", "#FFC878", "#FF9600", "#FF0000", "#780000", "#FF00FF", "#8C3CFF", "#000078"],n_colors=11)
    
def plot_day_evolution(df, folder_output_dir: str, logger, laeq_column:str, plotname:str):
    """ Line plots for each day
    Args:
        df (_type_): DataFrame
        folder_output_dir (str): Output directory
        logger (_type_): Logger
        laeq_column (str): Name of the column to use, typically LAeq
        plotname (str): Prefix to name the plot
    """
    try:
        sns.set_style("whitegrid")
        sns.set_palette("tab10")
        
        weekdays = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        df['day_name'] = pd.Categorical(df['day_name'], categories=weekdays, ordered=True)

        fig = sns.relplot(data=df,
                        x="hour",
                        y=laeq_column,
                        kind="line", 
                        hue="day_name", # hue is the column to split the data
                        estimator=leq,  # estimator is the function to apply to the data
                        aspect=1.3, # aspect is the width/height ratio
                        # legend=None,
                        )

        fig.set(xlim=(0, 23), ylim=(30, 105))
        plt.xticks(range(0, 24), [str(hour) for hour in range(0, 24)])
        plt.yticks(range(30, 105, 5), [str(level) for level in range(30, 105, 5)])
        
        for ax in fig.axes.flat:
            ax.spines['top'].set_visible(True)
            ax.spines['right'].set_visible(True)
        
        plt.axvline(x=7, color=".7", dashes=(2, 1), zorder=0)
        plt.axvline(x=19, color=".7", dashes=(2, 1), zorder=0)
        plt.axvline(x=23, color=".7", dashes=(2, 1), zorder=0)
        
        plt.text(s="Ln", x=0.13, y=0.97, transform=plt.gca().transAxes, c="Black", weight="bold")
        plt.text(s="Ld", x=0.53, y=0.97, transform=plt.gca().transAxes, c="Black", weight="bold")
        plt.text(s="Le", x=0.89, y=0.97, transform=plt.gca().transAxes, c="Black", weight="bold")
        
        plt.title(f"Evolución día {plotname} Date {df['date'][0]} - {df['date'][-1]}", fontsize=14)
        plt.ylabel('dB(A)')
        plt.xlabel('Hora')

        logger.info(f"Day evolution plot created for {plotname} Date {df['date'][0]} - {df['date'][-1]}")
        
        os.makedirs(folder_output_dir, exist_ok=True)
        fig.savefig(f"{folder_output_dir}/{plotname}_day_evolution.png", dpi=300)
        df.to_excel(f"{folder_output_dir}/{plotname}_day_evolution.xlsx")

        plt.close()

        logger.info(f"Day evolution plot saved to {folder_output_dir}/{plotname}_day_evolution.png")
        logger.info(f"Day evolution data saved to {folder_output_dir}/{plotname}_day_evolution.xlsx")

    except Exception as e:
        logger.error(f"Error in plot_day_evolution: {e}")

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
        df_indicadores = (df.groupby(['date','indicador_str'])['Fecha'].agg(['first','last']))
        df_indicadores['duration'] = df_indicadores.apply(lambda row: calculate_duration(row['first'], row['last']), axis=1)
        
        first_ld = df_indicadores[df_indicadores.index.get_level_values('indicador_str') == 'Ld'].iloc[0]
        first_ld_duration = calculate_duration(first_ld['first'], first_ld['last'])
        logger.info(f"First day {first_ld.name[0]} duration: {first_ld_duration}")
        
        last_le = df_indicadores[df_indicadores.index.get_level_values('indicador_str') == 'Le'].iloc[-1]
        last_le_duration = calculate_duration(last_le['first'], last_le['last'])
        logger.info(f"Last day {last_le.name[0]} duration: {last_le_duration}")
               
        first_day = first_ld.name[0]
        last_dat = last_le.name[0]
        
        if first_ld_duration <= LD_SECONDS:
            df = df[df['date'] != first_day]
            logger.info(f"First day {first_day} removed, less than {LD_SECONDS} seconds")
        if last_le_duration <= LE_SECONDS:
            df = df[df['date'] != last_dat]
            logger.info(f"Last day {last_dat} removed, less than {LE_SECONDS} seconds")
        
        indicadores_table = pd.pivot_table(data=df,index="date",columns="indicador_str",values=ind_column,aggfunc=leq).round(1)

        desired_order = ["Ln", "Ld", "Le"]
        indicadores_table = indicadores_table.reindex(columns=desired_order)

        plt.figure(figsize=(10, 8))
        
        ax = sns.heatmap(indicadores_table, annot=True, fmt=".1f", linewidth=0.5, cmap=cmap_dict, vmin=30, vmax=85)
        ax.set_yticklabels(ax.get_yticklabels(), rotation=0)
        
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