from mpl_finance import candlestick_ohlc
import matplotlib.pyplot as plt
import matplotlib.dates as mdates


def plot_candlestick(df, ax=None, fmt="%Y-%m-%d"):
    if ax is None:
        fig, ax = plt.subplots()
    idx_name = df.index.name
    print(idx_name)
    dat = df.reset_index()[[idx_name, "Open", "High", "Low", "Close"]]
    dat[df.index.name] = dat[df.index.name].map(mdates.date2num)
    ax.xaxis_date()
    ax.xaxis.set_major_formatter(mdates.DateFormatter(fmt))
    plt.xticks(rotation=45)
    _ = candlestick_ohlc(ax, dat.values, width=.6, colorup='g', alpha = 1)
    ax.set_xlabel(idx_name)
    ax.set_ylabel("OHLC")
    return ax


def plot_circle(x,y):
    circle = plt.Circle((mdates.date2num(x), y), 1, color='blue')
    ax=plt.gca()
    ax.add_artist(circle)


def plot_rectangle(startTime, endTime, low, high, color, text):
    #print("plot rectangle: startTime {} endTime {} low {} high {} color {}".format(startTime, endTime, low, high, color))
    from matplotlib.patches import Rectangle
    #convert to matplotlib date representation
    start = mdates.date2num(startTime)
    end = mdates.date2num(endTime)
    width = end - start
    height = high - low

    rect = Rectangle((start, low), width, height, color=color, alpha=0.4)
    rx, ry = rect.get_xy()
    cx = rx + rect.get_width()/2.0
    cy = ry + rect.get_height()/2.0
    ax = plt.gca()
    ax.annotate(text, (cx, cy), color='w', weight='bold', fontsize=6, ha='center', va='center')

    ax.add_patch(rect)
