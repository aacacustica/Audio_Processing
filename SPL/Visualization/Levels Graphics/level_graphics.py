import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
import numpy as np
import argparse
 
def leq(levels):
    # Filter out NaN values and ensure all values are floats
    levels = np.array(levels.dropna(), dtype=float)
    if len(levels) == 0:
        return np.nan
    return 10 * np.log10(np.mean(np.power(10, levels / 10)))

def plot_heatmap(df, values_column: str, agg_func: callable, plotname: str):
    df['day'] = df['date'].dt.date
    df['hour'] = df['date'].dt.hour
    leq_day_hour = pd.pivot_table(df, values=values_column, index=['day'], columns=['hour'], aggfunc=agg_func).round(1)
    plt.figure(figsize=(20, 5))
    sns.heatmap(leq_day_hour, cmap='viridis', annot=True, fmt='.1f')
    plt.xlabel('Hour')
    plt.ylabel('Day')
    plt.tight_layout()
    plt.savefig(f'{plotname}_heatmap.png', dpi=150)
    leq_day_hour.to_excel(f'{plotname}_heatmap_table_day_hour.xlsx')
    plt.close()

def make_timeplot(df, columns_dict: dict, agg_period: int, plotname: str):
    for col in columns_dict.values():
        df[col] = pd.to_numeric(df[col], errors='coerce')
    df.dropna(subset=[columns_dict['LAEQ_COLUMN']], inplace=True)
    df.set_index('date', inplace=True)
    
    leq_agg = df.resample(f'{agg_period}s').agg({columns_dict['LAEQ_COLUMN']: leq})
    lmax_agg = df.resample(f'{agg_period}s').agg({columns_dict['LAMAX_COLUMN']: 'max'})
    lmin_agg = df.resample(f'{agg_period}s').agg({columns_dict['LAMIN_COLUMN']: 'min'})
    
    L90 = df[columns_dict['LAEQ_COLUMN']].resample(f'{agg_period}s').quantile(0.1)
    L10 = df[columns_dict['LAEQ_COLUMN']].resample(f'{agg_period}s').quantile(0.9)
    
    fig, ax = plt.subplots(figsize=(20, 10))
    ax.set_facecolor("white")
    
    x = leq_agg.index
    ax.plot(x, leq_agg.values, linewidth=3, color='red')
    ax.plot(x, lmax_agg.values, linewidth=0.8, color='green')
    ax.plot(x, lmin_agg.values, linewidth=0.8, color='blue')
    ax.plot(x, L90, linewidth=0.8, color='#525252')
    ax.plot(x, L10, linewidth=0.8, color='#8497B0')

    hours = mdates.HourLocator(interval=1)
    h_fmt = mdates.DateFormatter('%H:%M')
    ax.xaxis.set_major_locator(hours)
    ax.xaxis.set_major_formatter(h_fmt)

    plt.ylabel('dB(A)')
    plt.xlabel('Hour')
    plt.xticks(rotation=45)
    plt.ylim([30, 120])
    plt.legend(['Leq', 'Lmax', 'Lmin', 'L90', 'L10'], bbox_to_anchor=(1.1, 1.05))
    
    plt.tight_layout()
    plt.savefig(f'{plotname}_{agg_period}s_timeplot.png', dpi=150)
    plt.close()

def arg_parser():
    parser = argparse.ArgumentParser(description='Plotting AudioMoth data')
    parser.add_argument('-f', '--csv-file', type=str, required=True, help='CSV file with AudioMoth data')
    parser.add_argument('-a', '--agg_period', type=int, required=False, default=3600, help='Aggregation period in seconds')
    return parser.parse_args()

def main():
    args = arg_parser()
    csv_file = args.csv_file
    agg_period = args.agg_period

    df = pd.read_csv(csv_file)
    df['date'] = pd.to_datetime(df['date'])
    
    columns_dict = {
        'LAEQ_COLUMN': 'LA',
        'LAMAX_COLUMN': 'LAmax',
        'LAMIN_COLUMN': 'LAmin'
    }
    
    # Ensure that the LA column is a float and not string
    df[columns_dict['LAEQ_COLUMN']] = df[columns_dict['LAEQ_COLUMN']].apply(lambda x: float(str(x).replace(',', '.')))

    # Generate heatmap
    plotname = csv_file.split('.')[0]  # Use the CSV filename as the plotname prefix
    plot_heatmap(df, 'LA', leq, plotname)

    # Generate timeplot
    make_timeplot(df, columns_dict, agg_period, plotname)

if __name__ == "__main__":
    main()
