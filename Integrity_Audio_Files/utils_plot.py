from matplotlib import pyplot as plt
import pandas as pd

def plot_results(metadata, location, logger):
    """
    Plotting the results
    """
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
    
    plt.figure(figsize=(20, 10))
    plt.plot(df.index, df['temperature'])
    plt.xlabel('Date')
    plt.ylabel('Temperature')
    plt.title(f'Temperature in {location}')


    plt.show()