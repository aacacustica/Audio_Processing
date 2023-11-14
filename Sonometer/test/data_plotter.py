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
    
def make_timeplot(df, folder_output_dir: str, logger, columns_dict: dict, agg_period: int, plotname: str, percentiles: bool):
    """ Plot Indicator time evolution in the measurument period 
    Args:
        df (_type_): DataFrame
        folder_output_dir (str): Output directory
        logger (_type_): Logger
        columns_dict (dict): Dictionary with the columns names
        agg_period (int): Aggregation period in seconds
        plotname (str): Prefix to name the plot
        percentiles (bool): If True, plot percentiles
    """
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
    
    hours = mdates.HourLocator(interval=2)
    h_fmt = mdates.DateFormatter('%d-%m-%y %H-%M')
    ax.xaxis.set_major_locator(hours)
    ax.xaxis.set_major_formatter(h_fmt)
    
    plt.xlim(df.index.min(), df.index.max())
    
    #plt.title(f'{plotname} Nivel equivalente {agg_period}s')
    plt.ylabel('dB(A)')
    plt.xlabel('Hora')
    plt.title(f'{plotname} Nivel equivalente {agg_period}s')
    plt.xticks(rotation=90)
    plt.ylim([30,105])
    plt.legend(['LAeq','Lmax','Lmin','L1','L5','L10','L90','L50'], bbox_to_anchor=(1.1, 1.05))
    plt.tight_layout()
    
    os.makedirs(f'{folder_output_dir}', exist_ok=True)
    plt.savefig(f'{folder_output_dir}/{plotname}_{agg_period}s_timeplot.png',dpi=150)
    leq_agg.to_excel(f'{folder_output_dir}/{plotname}_{agg_period}s_timeplot.xlsx')
    
    plt.close()
    
    logger.info(f"Timeplot saved to {folder_output_dir}/{plotname}_{agg_period}s_timeplot.png")
    logger.info(f"Timeplot data saved to {folder_output_dir}/{plotname}_{agg_period}s_timeplot.xlsx")

def plot_indheatmap(df, folder_output_dir: str, logger, plotname:str, ind_column:str):
    """Plot heatmap of pivot table with hour evolution of each day
    Args:
        df (_type_): DataFrame
        folder_output_dir (str): Output directory
        logger (_type_): Logger
        plotname (str): Prefix to name the plot
        ind_column (str): Name of the column to use, tipycally LAeq
    """
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