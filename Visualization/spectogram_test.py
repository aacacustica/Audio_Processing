import matplotlib.dates as mdates
import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker


def plt_spectrogram(df, folder_output_dir, plotname):
    print(df)
    frequency_columns = df.columns[5:-2]
    frequencies = [float(col.replace('Hz', '').replace('k', '000')) for col in frequency_columns]
    
    times = pd.to_datetime(df['date'])

    # select datatime from 22:30 to 23:30 of just one day
    df = df[(df['date'] >= '2024-07-09 22:30:00') & (df['date'] <= '2024-07-09 23:30:00')]
    times = pd.to_datetime(df['date'])

    spectrogram_data = df[frequency_columns].T.values
    spectrogram_data = spectrogram_data.clip(20, 110)
    freq_labels = [f"{freq} Hz" for freq in frequencies]
    
    plt.figure(figsize=(20, 10))
    plt.pcolormesh(times, frequencies, spectrogram_data, shading='auto', cmap='inferno')
    plt.colorbar(label='Magnitude (dB)')

    plt.yticks(frequencies, freq_labels)
    plt.ylabel('Frequency (Hz)')

    plt.xlabel('Time')
    plt.title(f'Spectrogram: {plotname}')
    plt.yscale('log')
    plt.ylim([min(frequencies), max(frequencies)])

    plt.gca().xaxis.set_major_locator(mdates.MinuteLocator(interval=300))
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M'))

    plt.xticks(rotation=90)
    plt.tight_layout()
    plt.show()

    # Save the plot
    # output_file = f'{folder_output_dir}/{plotname}_spectrogram.png'
    # plt.savefig(output_file, dpi=150)
    # plt.close()
    # print(f"Spectrogram saved to {output_file}")



def main():
    oct_file_path = r"\\192.168.205.117\AAC_Server\TRAFICO\23129_LEBER_GAUTXORI\3-Medidas\P1_Fueros\AUDIOMOTH\leq_oct_P1_Fueros_v2_0.csv"
    print("Reading file...")
    df = pd.read_csv(oct_file_path)
    # print(df)

    print("Plotting spectrogram...")
    plotname = oct_file_path.split("\\")[-3]
    folder_output_dir = oct_file_path.replace("3-Medidas", "5-Resultados")
    # get the path until the 5-Resultados folder
    folder_output_dir = "\\".join(folder_output_dir.split("\\")[:-3])
    
    # join folders
    folder_output_dir = os.path.join(folder_output_dir, plotname, "SPL", "Graphics_AUDIOMOTH", "Spectrogram")
    os.makedirs(folder_output_dir, exist_ok=True)
    print(f"Folder created {folder_output_dir}")

    plt_spectrogram(df, folder_output_dir, plotname)

if __name__ == "__main__":
    main()