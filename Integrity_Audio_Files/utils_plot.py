from matplotlib import pyplot as plt
import pandas as pd
import os

def plot_results(metadata, metadata_result_path, location, logger):
    """
    Plotting the results
    """
    matadata_folder = "METADATA"
    print(f"\n\nmetadata_result_path: {metadata_result_path}")
    # remove the last folder from the path

    metadata_result_path = os.path.dirname(metadata_result_path)
    print(f"\n\nmetadata_result_path: {metadata_result_path}")

    # get the path of the metadata folder
    metadata_folder_path = os.path.join(metadata_result_path, matadata_folder)

    print(f"\n\nPlotting temperature in {location}")
    print(f"Printing metadata: \n{metadata}")

    df = pd.DataFrame.from_dict(metadata, orient='index')
    print(f"\nThis is the original df: \n{df}")

    # convert 'date_UTC1' to datetime
    df['date_UTC1'] = pd.to_datetime(df['date_UTC1'])
    
    # set index to 'date_UTC1'
    df.set_index('date_UTC1', inplace=True)
    
    # sort the index
    df.sort_index(inplace=True)
    
    print(f"\nThis is the sorted df: \n{df}")

    # save the df to a csv file
    df.to_csv(f"{metadata_result_path}/{location}_metadata_clean.csv")
    print(f"\n{location}_metadata.csv saved in {metadata_result_path}")


    print(f"\n\nPlotting battery voltage in {location}")
    # plot the results
    plt.figure(figsize=(20, 10))

    # plot the battery voltage in bars
    plt.bar(df.index, df["battery_v"], color="black")
    # color bar
    plt.colorbar()

    # plt.scatter(df.index, df["battery_v"], c=df["battery_v"], cmap="inferno")
    
    plt.ylabel("Battery Voltage (V)")
    plt.xlabel("Time")
    plt.show()
    plt.close()
