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

    # first date withouth time
    first_date = df.index[0].strftime("%Y-%m-%d")
    last_date = df.index[-1].strftime("%Y-%m-%d")

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


def plot_all_at_one(df, metadata_folder_path, location, logger):
    """
    Plotting the battery voltage over time with color changes for high and low levels.
    """
    print(df)
    
    df.index = pd.to_datetime(df.index)

    # first date withouth time
    first_date = df.index[0].strftime("%Y-%m-%d")
    last_date = df.index[-1].strftime("%Y-%m-%d")

    print(f"\nPlotting temperature and battery voltage in {location}")
    
    plt.figure(figsize=(20, 10))

    # set two y axis for temperature and battery
    ax1 = plt.gca()
    ax2 = ax1.twinx()

    # Plot the battery voltage
    ax2.plot(df.index, df['battery_v'], color='blue', label='Battery Voltage')
    ax2.set_xlabel('Time')
    ax2.set_ylabel('Battery Voltage (V)')
    ax2.tick_params(axis='y')

    # Plot the temperature
    ax1.plot(df.index, df['temperature'], color='red', label='Temperature')
    ax1.set_ylabel('Temperature (Celsius)')
    ax1.tick_params(axis='y')

    plt.title(f'Battery Voltage and Temperature in {location} from {first_date} to {last_date}')

    # time interval
    plt.gca().xaxis.set_major_locator(mdates.HourLocator(interval=9))
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H:%M'))

    # rotate and align the tick labels so they look better
    fig = plt.gcf()
    fig.autofmt_xdate()

    # save the plot
    plt.savefig(f"{metadata_folder_path}/{location}_battery_temperature.png")

    plt.show()