import matplotlib.dates as mdates


def configure_time_axis(axis,timezone_name:str,*,max_ticks:int = 10) -> None:

    locator = mdates.AutoDateLocator(minticks=3,maxticks=max_ticks,tz=timezone_name)

    axis.xaxis.set_major_locator(locator)
    axis.xaxis.set_major_formatter(mdates.ConciseDateFormatter(locator,tz=timezone_name))
    axis.tick_params(axis='x',labelrotation=45)