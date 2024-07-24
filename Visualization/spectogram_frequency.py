import matplotlib.dates as mdates
import os
import pandas as pd
import matplotlib.pyplot as plt

def plt_frequency_band(df, folder_output_dir, plotname, target_frequency):
    frequency_columns = df.columns[5:-2]
    frequencies = [float(col.replace('Hz', '').replace('k', '000')) for col in frequency_columns]
    target_frequency_str = f"{target_frequency}Hz"

    df = df[(df['date'] >= '2024-07-09 22:30:00') & (df['date'] <= '2024-07-09 23:30:00')]
    times = pd.to_datetime(df['date'])

    if target_frequency_str in frequency_columns:
        frequency_data = df[target_frequency_str].values
    else:
        print(f"Frequency {target_frequency_str} not found in the columns.")
        return

    plt.figure(figsize=(20, 10))
    plt.plot(times, frequency_data, color='blue', label=f'{target_frequency} Hz')
    plt.ylabel('Magnitude (dB)')
    plt.xlabel('Time')
    plt.title(f'{plotname} - Frequency {target_frequency} Hz')
    plt.ylim([20, 110])
    plt.xticks(rotation=90)
    plt.legend(loc='upper right')

    # Customize x-axis for better readability
    plt.gca().xaxis.set_major_locator(mdates.MinuteLocator(interval=10))
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M'))
    plt.tight_layout()
    plt.show()

    # Save the plot
    output_file = f'{folder_output_dir}/{plotname}_frequency_{target_frequency}.png'
    plt.savefig(output_file, dpi=150)
    plt.close()
    print(f"Frequency plot saved to {output_file}")

def main():
    oct_file_path = r"\\192.168.205.117\AAC_Server\TRAFICO\23129_LEBER_GAUTXORI\3-Medidas\P1_Fueros\AUDIOMOTH\leq_oct_P1_Fueros_v2_0.csv"
    print("Reading file...")
    df = pd.read_csv(oct_file_path)

    print("Plotting frequency band...")
    plotname = oct_file_path.split("\\")[-3]
    folder_output_dir = oct_file_path.replace("3-Medidas", "5-Resultados")
    # Get the path until the 5-Resultados folder
    folder_output_dir = "\\".join(folder_output_dir.split("\\")[:-3])
    
    # Join folders
    folder_output_dir = os.path.join(folder_output_dir, plotname, "SPL", "Graphics_AUDIOMOTH", "FrequencyBand")
    os.makedirs(folder_output_dir, exist_ok=True)
    print(f"Folder created {folder_output_dir}")

    target_frequency = '3174.80'
    plt_frequency_band(df, folder_output_dir, plotname, target_frequency)

if __name__ == "__main__":
    main()
