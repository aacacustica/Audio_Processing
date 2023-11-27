import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
from time_level_utils import *
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
        
        # translate the day name to spanish from english in day_name
        df['Día'] = df['day_name'].replace(['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'], ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo'])
        
        weekdays = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
        df['Día'] = pd.Categorical(df['Día'], categories=weekdays, ordered=True)
        
        fig = sns.relplot(
            data=df,
            x="hour",
            y=laeq_column,
            kind="line", # kind is the type of plot to draw
            hue="Día", # hue is the column to split the data
            estimator=leq,  # estimator is the function to apply to the data
            aspect=1.3, # aspect is the width/height ratio
            palette=C_MAP_WEEKDAY,
        )

        fig.set(xlim=(-1, 24), ylim=(30, 105))

        # Change the x-axis labels to 24-hour format
        hour_labels = [f"{hour:02d}:00" for hour in range(24)]
        plt.xticks(range(24), hour_labels, rotation=90)

        plt.yticks(range(30, 105, 5), [str(level) for level in range(30, 105, 5)])

        for ax in fig.axes.flat:
            ax.spines['top'].set_visible(True)
            ax.spines['right'].set_visible(True)
        
        plt.axvline(x=6.50, color=".7", dashes=(2, 1), zorder=0)  # 6:45 AM
        plt.axvline(x=18.50, color=".7", dashes=(2, 1), zorder=0)  # 6:45 PM
        plt.axvline(x=22.50, color=".7", dashes=(2, 1), zorder=0)  # 10:45 PM

        plt.text(s="Ln", x=0.13, y=0.97, transform=plt.gca().transAxes, c="Black", weight="bold")
        plt.text(s="Ld", x=0.53, y=0.97, transform=plt.gca().transAxes, c="Black", weight="bold")
        plt.text(s="Le", x=0.85, y=0.97, transform=plt.gca().transAxes, c="Black", weight="bold")
        plt.text(s="Ln", x=0.96, y=0.97, transform=plt.gca().transAxes, c="Black", weight="bold")
        
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
    try:
        sns.set_style("whitegrid")
        sns.set_palette("tab10")
        
        # translate the day name to spanish from english in day_name
        df['Día'] = df['day_name'].replace(['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'], ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo'])
        
        weekdays = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
        df['Día'] = pd.Categorical(df['Día'], categories=weekdays, ordered=True)
        
        for ind in df["indicador_str"].unique():
            if ind == 'Ln':
                continue
            
            df_temp = df[df["indicador_str"] == ind]
            
            fig = sns.relplot(
                data=df_temp,
                x="hour",
                y=laeq_column,
                kind="line", # kind is the type of plot to draw
                hue="Día", # hue is the column to split the data
                estimator=leq,  # estimator is the function to apply to the data
                aspect=1.3, # aspect is the width/height ratio
                palette=C_MAP_WEEKDAY,
            )
            
            if ind == 'Ld':
                fig.set(xlim=(6, 19), ylim=(30, 105))
                plt.xticks(range(7, 19), [f"{hour:02d}:00" for hour in range(7, 19)])
                logger.info(f"Plotted Ld")
                
            elif ind == 'Le':
                fig.set(xlim=(18.7, 22.3), ylim=(30, 105))  # Adjust xlim to be tighter
                plt.xticks([18.7, 19, 20, 21, 22, 22.3], ['', '19:00', '20:00', '21:00', '22:00', ''])  # Adjust xticks to match the new xlim
                logger.info(f"Ploted Le")

            plt.yticks(range(30, 105, 5), [str(level) for level in range(30, 105, 5)])

            for ax in fig.axes.flat:
                ax.spines['top'].set_visible(True)
            
            ax.spines['right'].set_visible(True)
            plt.title(f"Evolución {ind}")
            plt.ylabel('dB(A)')
            plt.xlabel('Hora')
        
            os.makedirs(f'{folder_output_dir}', exist_ok=True)
            fig.savefig(f"{folder_output_dir}/{plotname}_{ind}_evolution.png",dpi=150)
            df_temp.to_excel(f"{folder_output_dir}/{plotname}_{ind}_evolution.xlsx")
        
            plt.close()
        
        logger.info(f"Period evolution plot saved to {folder_output_dir}/{plotname}_{ind}_evolution.png")
        logger.info(f"Period evolution data saved to {folder_output_dir}/{plotname}_{ind}_evolution.xlsx")
    
    except Exception as e:
        logger.error(f"Error in plot_period_evolution: {e}")

def plot_night_evolution(df, folder_output_dir: str, logger, laeq_column:str, plotname:str, indicador_noche:str):
    """Plot night evolution of the measurement period.
    Args:
        df (_type_): DataFrame
        folder_output_dir (str): Output directory
        logger (_type_): Logger
        laeq_column (str): Name of the column to use, tipycally LAeq
        plotname (str): Prefix to name the plot    
    """
    try:
        sns.set_style("whitegrid")
        sns.set_palette("tab10")
        
        df['Día'] = df['night_str']
        
        df['date'] = pd.to_datetime(df['date'])
        df.sort_values(by=['date', 'hour'], inplace=True)

        night_data = pd.DataFrame()
        unique_dates = df['date'].dt.date.unique()

        for current_date in unique_dates:
            next_date = current_date + pd.Timedelta(days=1)
            data_23 = df[(df['date'].dt.date == current_date) & (df['hour'] == 23)]
            data_00_06 = df[(df['date'].dt.date == next_date) & (df['hour'].isin(range(0, 7)))]

            if not data_23.empty and not data_00_06.empty:
                combined_data = pd.concat([data_23, data_00_06])
                night_data = pd.concat([night_data, combined_data])

        night_data['plot_hour'] = night_data['hour'].replace({23: -1}).astype(int)
        night_data.sort_values(by=['date', 'plot_hour'], inplace=True)
        
        # save to excel
        os.makedirs(folder_output_dir, exist_ok=True)
        night_data.to_excel(f"{folder_output_dir}/{plotname}_{indicador_noche}_evolution.xlsx")
        logger.info(f"Night evolution data saved to {folder_output_dir}/{plotname}_{indicador_noche}_evolution.xlsx")

        fig = sns.relplot(
            data=night_data, 
            x="plot_hour", 
            y=laeq_column, 
            kind="line", 
            hue="Día",
            estimator=leq, 
            aspect=1.3,
            palette=C_MAP_WEEKDAY_NIGHT
        )
        
        plt.xticks(range(-1, 7), ['23:00', '00:00', '01:00', '02:00', '03:00', '04:00', '05:00', '06:00'])
        plt.yticks(range(30, 105, 5), [str(level) for level in range(30, 105, 5)])

        plt.xlim(-1.5, 6.5)

        for ax in fig.axes.flat:
            ax.spines['top'].set_visible(True)
            ax.spines['right'].set_visible(True)

        plt.title(f'Evolución {indicador_noche}')
        plt.ylabel('dB(A)')
        plt.xlabel('Hora')

        os.makedirs(folder_output_dir, exist_ok=True)
        fig.savefig(f"{folder_output_dir}/{plotname}_{indicador_noche}_evolution.png", dpi=150)
        logger.info(f"Night evolution plot saved to {folder_output_dir}/{plotname}_{indicador_noche}_evolution.png")
    
    except Exception as e:
        logger.error(f"Error in plot_night_evolution: {e}")


def plot_night_evolution_15_min(df, folder_output_dir: str, logger, name_extension, laeq_column:str, plotname:str, indicador_noche:str):
    """Plot night evolution of the measurement period.
    Args:
        df (_type_): DataFrame
        folder_output_dir (str): Output directory
        logger (_type_): Logger
        name_extension (str): Extension to name the plot
        laeq_column (str): Name of the column to use, tipycally LAeq
        plotname (str): Prefix to name the plot    
    """
    try:
        sns.set_style("whitegrid")
        sns.set_palette("tab10")
        
        # rename the day name to spanish from english in 'night_str'
        df['Día'] = df['night_str']

        df.index = pd.to_datetime(df.index)

        df_resampled = df.resample('15T')[laeq_column].mean()
        # print(f"This is the df resampled: \n{df_resampled}")
        
        df_night_str = df.resample('15T')['Día'].agg(lambda x: x.value_counts().index[0])
        df_resampled = pd.DataFrame(df_resampled).join([df_night_str])
        
        # Add date and time columns
        df_resampled['date'] = df_resampled.index.date
        df_resampled['time'] = df_resampled.index.time
        
        # Convert 'time' to a plottable format with a 15-minute offset
        df_resampled['plot_time'] = [(t.hour * 60 + t.minute - 15) - (23 * 60) if t.hour >= 23 else (t.hour * 60 + t.minute - 15) + 60 for t in df_resampled['time']]

        # Filter the data
        unique_dates = pd.to_datetime(df_resampled.index.date).unique()
        night_data = pd.DataFrame()

        # Get the data for each night
        for current_date in unique_dates:
            # Get the start time, which is the last 15-minute interval of the previous day
            start_time = pd.Timestamp(current_date - pd.Timedelta(days=1)).replace(hour=23, minute=0)
            # Get the end time, which is the first 6 hours and 45 minutes of the current day
            end_time = pd.Timestamp(current_date).replace(hour=6, minute=45)
            # slice the data, which is the last 15-minute interval of the previous day and the first 6 hours and 45 minutes of the current day
            data_slice = df_resampled[start_time:end_time]
            
            # if the slice is not empty and the minimum index hour is 23, then it is a night
            if not data_slice.empty and data_slice.index.min().hour == 23:
                # so we add it to the night data
                night_data = pd.concat([night_data, data_slice])
        
        # print(f"This is the night data: \n{night_data}")
        #save to excel
        os.makedirs(folder_output_dir, exist_ok=True)
        night_data.to_excel(f"{folder_output_dir}/{plotname}_{indicador_noche}_evolution_{name_extension}.xlsx")
        logger.info(f"Night evolution data saved to {folder_output_dir}/{plotname}_{indicador_noche}_evolution_{name_extension}.xlsx")
        
        # Create the plot
        fig = sns.relplot(
                data=night_data, 
                x="plot_time", 
                y=laeq_column, 
                kind="line", 
                hue="Día",
                estimator=leq, 
                aspect=1.3,
                palette=C_MAP_WEEKDAY_NIGHT
            )

        # Setting x-axis labels
        x_labels = [f'{hour:02d}:{minute:02d}' for hour in range(23, 24) for minute in range(0, 60, 15)] + \
                [f'{hour:02d}:{minute:02d}' for hour in range(0, 7) for minute in range(0, 60, 15)]
                
        x_ticks = range(-15, 465, 15)
        plt.xticks(x_ticks, x_labels, rotation=90)
        plt.yticks(range(30, 105, 5), [str(level) for level in range(30, 105, 5)])
        
        # Set plot limits and labels
        plt.xlim(-30, 465)
        
        for ax in fig.axes.flat:
            ax.spines['top'].set_visible(True)
            ax.spines['right'].set_visible(True)
        
        plt.title(f'Evolución {indicador_noche} cada 15 minutos')
        plt.ylabel('dB(A)')
        plt.xlabel('Hora')

        # Save the plot
        fig.savefig(os.path.join(folder_output_dir, f'{plotname}_{indicador_noche}_evolution_{name_extension}.png'))
        logger.info(f"Night evolution plot saved to {folder_output_dir}/{plotname}_{indicador_noche}_evolution_{name_extension}.png")
    except Exception as e:
        logger.error(f"Error in plot_night_evolution_15_min: {e}")

def plot_heatmap_evolution(df, folder_output_dir: str, logger, values_column: str, agg_func: str, plotname:str):
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
        leq_day_hour = pd.pivot_table(
            df, 
            values=values_column, 
            index=['date'],
            columns=['hour'], 
            aggfunc=agg_func
        ).round(1)
        
        leq_day_hour.columns = [f"{hour:02d}:00" for hour in leq_day_hour.columns]
        
        plt.figure(figsize=(20,5))
        
        sns.heatmap(
            leq_day_hour, 
            vmin=30, 
            vmax= 85, 
            cmap=cmap_dict, 
            annot=True
        )
        
        plt.xlabel('Hora')
        plt.ylabel('Día')
        plt.title(f'{plotname} Nivel equivalente')
        
        plt.yticks(rotation=0)
        plt.tight_layout()
        
        os.makedirs(f'{folder_output_dir}', exist_ok=True)
        plt.savefig(f'{folder_output_dir}/{plotname}_heatmap_evolucion.png',dpi=150)
        
        leq_day_hour.to_excel(f'{folder_output_dir}/{plotname}_heatmap_evolucion.xlsx')
        
        plt.close()
        
        logger.info(f"Heatmap plot saved to {folder_output_dir}/{plotname}_heatmap_evolucion.png")
        logger.info(f"Heatmap data saved to {folder_output_dir}/{plotname}_heatmap_evolucion.xlsx")
    except Exception as e:
        logger.error(f"Error in plot_heatmap: {e}")
        
def make_time_plot(df: pd.DataFrame, folder_output_dir: str, logger, columns_dict: dict, agg_period: int, plotname: str, percentiles: list):
    """
    Plot timeplot of the data for LAeq, Lmax, Lmin and percentiles.

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
        #oca = df.resample(f'{agg_period}s').agg({'oca': 'min'})

        plt.style.use('seaborn-whitegrid')
        fig, ax = plt.subplots(figsize=(20, 10))
        ax.set_facecolor("white")

        x = agg_data.index
        ax.plot(x, agg_data[columns_dict['LAEQ_COLUMN']], linewidth=3, color='red', label='LAeq')
        ax.plot(x, agg_data[columns_dict['LAMAX_COLUMN']], linewidth=1, color='#FF99FF', label='Lmax')
        ax.plot(x, agg_data[columns_dict['LAMIN_COLUMN']], linewidth=1, color='#92D050', label='Lmin')
        # OCA
        # #ax.plot(x, oca.values, color='#00B0F0')

        for percentile in percentiles:
            values = df[columns_dict['LAEQ_COLUMN']].resample(f'{agg_period}s').quantile((100 - percentile) / 100)
            ax.plot(
                x, 
                values, 
                linewidth=0.5, 
                label=f'L{percentile}', 
                color=PERCENTIL_COLOUR[percentile]
            )

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
        plt.savefig(f'{folder_output_dir}/{plotname}_{agg_period}s_time_plot.png', dpi=150)
        agg_data.to_excel(f'{folder_output_dir}/{plotname}_{agg_period}s_time_plot.xlsx')

        plt.close()

        logger.info(f"Timeplot saved to {folder_output_dir}/{plotname}_{agg_period}s_time_plot.png")
        logger.info(f"Timeplot data saved to {folder_output_dir}/{plotname}_{agg_period}s_time_plot.xlsx")
    except Exception as e:
        logger.error(f"Error in make_timeplot: {e}")

def plot_indicadores_heatmap(df, folder_output_dir: str, logger, plotname:str, ind_column:str):
    """Plot heatmap of pivot table with hour evolution of each day
    Args:
        df (_type_): DataFrame
        folder_output_dir (str): Output directory
        logger (_type_): Logger
        plotname (str): Prefix to name the plot
        ind_column (str): Name of the column to use, tipycally LAeq
    """
    try:
        if "Fecha" not in df.columns and "Date hour" in df.columns:
            # df["Fecha"] = df["Date hour"]
            df["Fecha"] = pd.to_datetime(df['Date hour'], dayfirst=True)
        
        if "Fecha" not in df.columns and "Time" in df.columns:
            df["Fecha"] = pd.to_datetime(df['Time'], dayfirst=True)

        df_indicadores = (df.groupby(['date','indicador_str'])['Fecha'].agg(['first','last']))
        df_indicadores['duration'] = df_indicadores.apply(lambda row: calculate_duration(row['first'], row['last']), axis=1)
        
        # Indicators to check
        indicators_to_check = ['Ld', 'Le', 'Ln']

        # Select the first and last day
        first_day = df['date'].min()
        last_day = df['date'].max()

        # Check the presence of indicators
        presence_first_day = {indicator: indicator in df[df['date'] == first_day]['indicador_str'].unique() for indicator in indicators_to_check}
        presence_last_day = {indicator: indicator in df[df['date'] == last_day]['indicador_str'].unique() for indicator in indicators_to_check}
        logger.info(f"Presence of indicators in first day {first_day}: {presence_first_day}")
        logger.info(f"Presence of indicators in last day {last_day}: {presence_last_day}")

        # Check duration of indicators
        duration_first_day = {indicator: df_indicadores.loc[(first_day, indicator), 'duration'] if presence_first_day[indicator] else 0 for indicator in indicators_to_check}
        duration_last_day = {indicator: df_indicadores.loc[(last_day, indicator), 'duration'] if presence_last_day[indicator] else 0 for indicator in indicators_to_check}
        
        # Log duration information
        for indicator in indicators_to_check:
            logger.info(f"Duration of {indicator} on the first day {first_day}: {duration_first_day[indicator]}")
            logger.info(f"Duration of {indicator} on the last day {last_day}: {duration_last_day[indicator]}")

        # Removal logic based on duration and presence
        for indicator in indicators_to_check:
            if presence_first_day[indicator] and duration_first_day[indicator] <= LE_SECONDS:
                df = df[~((df['date'] == first_day) & (df['indicador_str'] == indicator))]
                logger.info(f"{indicator} indicator from first day {first_day} removed, less than {LE_SECONDS} seconds")

            if presence_last_day[indicator] and duration_last_day[indicator] <= LE_SECONDS:
                df = df[~((df['date'] == last_day) & (df['indicador_str'] == indicator))]
                logger.info(f"{indicator} indicator from last day {last_day} removed, less than {LE_SECONDS} seconds")
        
        # make the energy average of the indicators
        indicadores_table = pd.pivot_table(
            data=df,
            index="date",
            columns="indicador_str",
            values=ind_column,
            aggfunc=leq
        ).round(1)

        desired_order = ["Ln", "Ld", "Le"]
        indicadores_table = indicadores_table.reindex(columns=desired_order)

        plt.figure(figsize=(10, 8))
        
        ax = sns.heatmap(
            indicadores_table, 
            annot=True, 
            fmt=".1f", 
            linewidth=0.5, 
            cmap=cmap_dict, 
            vmin=30, 
            vmax=85
        )
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
        
        # Indicador power average
        general_power_averages = indicadores_table.apply(leq).round(1)
        general_power_averages_df = general_power_averages.to_frame().transpose()
        
        os.makedirs(f'{folder_output_dir}', exist_ok=True)
        general_power_averages_df.to_excel(f'{folder_output_dir}/{plotname}_indicadores_generales.xlsx')
        logger.info(f"Indicadores generales data saved to {folder_output_dir}/{plotname}_indicadores_generales.xlsx")
    
    except Exception as e:
        logger.error(f"Error in plot_indheatmap: {e}")