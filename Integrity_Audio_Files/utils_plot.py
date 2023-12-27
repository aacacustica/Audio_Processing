from matplotlib import pyplot as plt
import pandas as pd
import matplotlib.dates as mdates
import os

def plot_temperature(df, metadata_folder_path, location, logger):
    """
    Plotting the results
    """
    # df index to datetime
    df.index = pd.to_datetime(df.index)

    # first date withouth time
    first_date = df.index[0].strftime("%Y-%m-%d")
    last_date = df.index[-1].strftime("%Y-%m-%d")

    # plot the results
    print(f"\n\nPlotting temperature in {location}")
    plt.figure(figsize=(20, 10))

    plt.scatter(df.index, df["temperature"], c=df["temperature"], cmap="inferno")
    plt.colorbar()
    
    plt.ylabel("Temperature (Celsius)")
    plt.xlabel("Time")
    plt.title(f"Temperature in {location} from {first_date} to {last_date}")

    # time interval
    plt.gca().xaxis.set_major_locator(mdates.HourLocator(interval=9))
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H:%M'))

    # rotate and align the tick labels so they look better
    fig = plt.gcf()
    fig.autofmt_xdate()

    # save the plot
    plt.savefig(f"{metadata_folder_path}/{location}_temperature.png")
    logger.info(f"Plot saved in {metadata_folder_path}/{location}_temperature.png")

    plt.show()


def plot_battery(df, metadata_folder_path, location, logger):
    """
    Plotting the battery voltage over time with color changes for high and low levels.
    """
    df.index = pd.to_datetime(df.index)

    print(f"\nPlotting battery voltage in {location}")
    plt.figure(figsize=(20, 10))

    # Plot the battery voltage
    plt.plot(df.index, df['battery_v'])  # 'marker' to mark each data point

    plt.xlabel('Time')
    plt.ylabel('Battery Voltage (V)')
    plt.title(f'Battery Voltage over Time in {location}')

    # time interval
    plt.gca().xaxis.set_major_locator(mdates.HourLocator(interval=9))
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H:%M'))

    # rotate and align the tick labels so they look better
    fig = plt.gcf()
    fig.autofmt_xdate()

    # save the plot
    plt.savefig(f"{metadata_folder_path}/{location}_battery.png")

    plt.show()





