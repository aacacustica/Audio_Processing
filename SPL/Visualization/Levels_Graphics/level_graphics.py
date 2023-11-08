import logging
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
import numpy as np
import argparse
import os

def setup_logging(output_dir):
    log_file = os.path.join(output_dir, 'level_graphics.log')
    logging.basicConfig(filename=log_file,
                        filemode='a', 
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                        level=logging.INFO)

def plt_name(plotname: str, logger):
    logger.debug(f"Original plot name: {plotname}")
    if "_spl" or "_spl_oct_" in plotname:
        plotname = plotname.split("_spl")[0]
    logger.debug(f"Processed plot name: {plotname}")
    return plotname

def leq(levels, logger):
    levels = np.array(levels.dropna(), dtype=float)
    if len(levels) == 0:
        logger.warning("Empty levels array received, returning NaN")
        return np.nan
    result = 10 * np.log10(np.mean(np.power(10, levels / 10)))
    logger.debug(f"Computed leq: {result}")
    return result

def plot_heatmap(df, values_column: str, agg_func: callable, output_dir: str, plotname: str, logger):
    logger.info(f"Starting heatmap plot for {plotname}")
    plotname = plt_name(plotname, logger)

    df['day'] = df['date'].dt.date
    df['hour'] = df['date'].dt.hour
    leq_day_hour = pd.pivot_table(df, values=values_column, index=['day'], columns=['hour'], aggfunc=agg_func).round(1)
    plt.figure(figsize=(20, 5))

    plt.title(f"{plotname.replace('_', ' ')}")
    
    sns.heatmap(leq_day_hour, cmap=sns.cubehelix_palette(), annot=True, fmt='.1f')  
    plt.xlabel('Hour')
    plt.ylabel('Day')
    plt.tight_layout()
    
    filepath = os.path.join(output_dir, f'{plotname}_heatmap.png')
    plt.savefig(filepath, dpi=150)
    logger.info(f"Heatmap for {plotname} saved to {filepath}")

    leq_day_hour.to_csv(os.path.join(output_dir, f'{plotname}_heatmap.csv'))
    
    plt.close()

def make_timeplot(df, columns_dict: dict, agg_period: int, plotname: str, output_dir: str, percentiles: list, logger):
    logger.info(f"Starting timeplot for {plotname}")
    plotname = plt_name(plotname, logger)

    for col in columns_dict.values():
        df[col] = pd.to_numeric(df[col], errors='coerce')
    df.dropna(subset=[columns_dict['LAEQ_COLUMN']], inplace=True)
    df.set_index('date', inplace=True)

    leq_with_logger = lambda x: leq(x, logger)
    
    leq_agg = df.resample(f'{agg_period}s').agg({columns_dict['LAEQ_COLUMN']: leq_with_logger})
    lmax_agg = df.resample(f'{agg_period}s').agg({columns_dict['LAMAX_COLUMN']: 'max'})
    lmin_agg = df.resample(f'{agg_period}s').agg({columns_dict['LAMIN_COLUMN']: 'min'})

    combined_df = pd.DataFrame(index=leq_agg.index)
    combined_df['Leq'] = leq_agg.values.flatten()
    combined_df['Lmax'] = lmax_agg.values.flatten()
    combined_df['Lmin'] = lmin_agg.values.flatten()

    for perc in percentiles:
        percentile_value = 1 - (perc / 100.0)
        percentile_data = df[columns_dict['LAEQ_COLUMN']].resample(f'{agg_period}s').quantile(percentile_value)
        combined_df[f'L{int(perc)}'] = percentile_data.values

    fig, ax = plt.subplots(figsize=(20, 10))
    ax.set_facecolor("white")
    plt.title(f"{plotname.replace('_', ' ')} | {agg_period}s")

    x = combined_df.index
    ax.plot(x, combined_df['Leq'], linewidth=3, color='red', label='Leq')
    ax.plot(x, combined_df['Lmax'], linewidth=0.8, color='#FF99FF', label='Lmax')
    ax.plot(x, combined_df['Lmin'], linewidth=0.8, color='#92D050', label='Lmin')

    for perc in percentiles:
        ax.plot(x, combined_df[f'L{int(perc)}'], linewidth=0.8, label=f'L{int(perc)}')

    hours = mdates.HourLocator(interval=2)
    h_fmt = mdates.DateFormatter('%H:%M')
    ax.xaxis.set_major_locator(hours)
    ax.xaxis.set_major_formatter(h_fmt)

    ax.set_xlim(df.index.min(), df.index.max())

    plt.ylabel('dB(A)')
    plt.xlabel('Hour')
    plt.xticks(rotation=90)
    plt.ylim([30, 120])
    plt.legend(bbox_to_anchor=(1.01, 1), loc='upper left')

    plt.tight_layout()
    fig_filepath = os.path.join(output_dir, f'{plotname}_{agg_period}s_timeplot.png')
    plt.savefig(fig_filepath, dpi=150)
    logger.info(f"Timeplot for {plotname} saved to {fig_filepath}")

    csv_filepath = os.path.join(output_dir, f'{plotname}_{agg_period}s_timeplot.csv')
    combined_df.to_csv(csv_filepath, index_label='Time')
    logger.info(f"CSV file for {plotname} saved to {csv_filepath}")

    plt.close()

def arg_parser():
    parser = argparse.ArgumentParser(description='Plotting AudioMoth data')
    parser.add_argument('-f', '--csv-file', type=str, required=True, help='CSV file with AudioMoth data')
    parser.add_argument('-a', '--agg_period', type=int, required=False, default=900, help='Aggregation period in seconds')
    parser.add_argument('-o', '--output-dir', type=str, required=False, default='.', help='Output directory')
    parser.add_argument('-p', '--percentiles', type=float, nargs='+', required=False, default=[90, 10], help='Percentiles to plot (L90 and L10 as default)')
    return parser.parse_args()

def main():
    args = arg_parser()
    csv_file = args.csv_file
    agg_period = args.agg_period
    output_dir = args.output_dir
    percentiles = args.percentiles

    input_dir = os.path.dirname(csv_file)
    output_dir = os.path.join(input_dir, 'Level_Graphics')
    os.makedirs(output_dir, exist_ok=True)

    setup_logging(output_dir)
    logger = logging.getLogger(__name__)
    logger.info(f"Script started with CSV file: {csv_file} and output directory: {output_dir}")

    try:
        input_dir = os.path.dirname(csv_file)
        output_dir = os.path.join(input_dir, 'Level_Graphics')
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            logger.info(f"Created output directory: {output_dir}")
        else:
            logger.info(f"Output directory already exists: {output_dir}")

        logger.info(f"Reading CSV file: {csv_file}")
        df = pd.read_csv(csv_file)
        df['date'] = pd.to_datetime(df['date'])

        columns_dict = {
            'LAEQ_COLUMN': 'LA',
            'LAMAX_COLUMN': 'LAmax',
            'LAMIN_COLUMN': 'LAmin'
        }

        df[columns_dict['LAEQ_COLUMN']] = df[columns_dict['LAEQ_COLUMN']].apply(lambda x: float(str(x).replace(',', '.')))

        plotname = csv_file.split('/')[-1].split('.')[0]
        plot_heatmap(df, 'LA', lambda x: leq(x, logger), output_dir, plotname, logger)
        make_timeplot(df, columns_dict, agg_period, plotname, output_dir, percentiles, logger)

        logger.info("Script completed successfully")

    except Exception as e:
        logger.exception(f"Error occurred: {e}")

if __name__ == "__main__":
    main()

