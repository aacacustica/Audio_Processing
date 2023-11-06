import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
import numpy as np
import argparse
import os

def plt_name(plotname: str):
    if "_spl" or "_spl_oct_" in plotname:
        plotname = plotname.split("_spl")[0]
    return plotname
 
def leq(levels):
    levels = np.array(levels.dropna(), dtype=float)
    if len(levels) == 0:
        return np.nan
    return 10 * np.log10(np.mean(np.power(10, levels / 10)))



def plot_heatmap(df, values_column: str, agg_func: callable, plotname: str, output_dir: str):
    plotname = plt_name(plotname)

    df['day'] = df['date'].dt.date
    df['hour'] = df['date'].dt.hour
    leq_day_hour = pd.pivot_table(df, values=values_column, index=['day'], columns=['hour'], aggfunc=agg_func).round(1)
    plt.figure(figsize=(20, 5))

    plt.title(f"{plotname.replace('_', ' ')}")
    
    sns.heatmap(leq_day_hour, cmap=sns.cubehelix_palette(), annot=True, fmt='.1f')  
    plt.xlabel('Hour')
    plt.ylabel('Day')
    plt.tight_layout()
    
    plt.savefig(os.path.join(output_dir, f'{plotname}_heatmap.png'), dpi=150)
    leq_day_hour.to_csv(os.path.join(output_dir, f'{plotname}_heatmap_table_day_hour.csv'))
    
    plt.close()



def make_timeplot(df, columns_dict: dict, agg_period: int, plotname: str, output_dir: str, percentiles: list):
    plotname = plt_name(plotname)

    for col in columns_dict.values():
        df[col] = pd.to_numeric(df[col], errors='coerce')
    df.dropna(subset=[columns_dict['LAEQ_COLUMN']], inplace=True)
    df.set_index('date', inplace=True)

    leq_agg = df.resample(f'{agg_period}s').agg({columns_dict['LAEQ_COLUMN']: leq})
    lmax_agg = df.resample(f'{agg_period}s').agg({columns_dict['LAMAX_COLUMN']: 'max'})
    lmin_agg = df.resample(f'{agg_period}s').agg({columns_dict['LAMIN_COLUMN']: 'min'})

    fig, ax = plt.subplots(figsize=(20, 10))
    ax.set_facecolor("white")
    plt.title(f"{plotname.replace('_', ' ')} | {agg_period}s")

    x = leq_agg.index
    ax.plot(x, leq_agg.values, linewidth=3, color='red', label='Leq')
    ax.plot(x, lmax_agg.values, linewidth=0.8, color='#FF99FF', label='Lmax')
    ax.plot(x, lmin_agg.values, linewidth=0.8, color='#92D050', label='Lmin')

    for perc in percentiles:
        percentile_value = 1 - (perc / 100.0)
        percentile_data = df[columns_dict['LAEQ_COLUMN']].resample(f'{agg_period}s').quantile(percentile_value)
        ax.plot(x, percentile_data, linewidth=0.8, label=f'L{int(perc)}')

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
    plt.savefig(os.path.join(output_dir, f'{plotname}_{agg_period}s_timeplot.png'), dpi=150)
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

    df = pd.read_csv(csv_file)
    df['date'] = pd.to_datetime(df['date'])

    columns_dict = {
        'LAEQ_COLUMN': 'LA',
        'LAMAX_COLUMN': 'LAmax',
        'LAMIN_COLUMN': 'LAmin'
    }

    df[columns_dict['LAEQ_COLUMN']] = df[columns_dict['LAEQ_COLUMN']].apply(lambda x: float(str(x).replace(',', '.')))

    plotname = csv_file.split('.')[0]  
    plot_heatmap(df, 'LA', leq, plotname, output_dir)
    make_timeplot(df, columns_dict, agg_period, plotname, output_dir, percentiles)

if __name__ == "__main__":
    main()
