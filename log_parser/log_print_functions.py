import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd


def plot_imem_iv(df):
    # Convert the 'Date' column to datetime format
    df_plot = df[(df["imem_se"] < 38158950)]
    df_plot["timestamp"] = pd.to_datetime(df_plot["timestamp"])

    df_plot["ratio_iv"] = df_plot["iv"] / df_plot["imem_se"]
    df_plot.loc[(df_plot["iv"] == 0) & (df_plot["imem_se"] == 0), "ratio_iv"] = 1

    # Plot multiple columns simultaneously
    fig, ax = plt.subplots()  # Create a figure and axes
    ax2 = ax.twinx()  # Create a twin Axes for ratio_iv

    df_plot.plot(
        x="timestamp",
        y=["imem_se", "iv"],
        kind="line",
        marker="o",
        linestyle="-",
        markersize=1,
        ax=ax,  # Specify the axes to plot on
    )

    df_plot.plot(
        x="timestamp",
        y="ratio_iv",
        color="red",
        marker=".",
        linestyle="",
        ax=ax2,  # Specify the axes to plot on
    )

    # Combine legends
    lines, labels = ax.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()

    # Change the labels
    labels[0] = "ECC"
    labels[1] = "IV"

    ax.legend(lines + lines2, labels + labels2, loc="lower right")

    ax2.legend().remove()
    # Add labels and title
    ax.set_xlabel("Coremark Executions")
    ax.set_ylabel("Detected Errors")
    ax2.set_ylabel("IV/ECC Ratio")
    plt.grid()

    # Remove x-axis tick labels
    plt.xticks([])

    # Show the plot
    plt.show()


def plot_column(df, column_name):
    # Convert the 'Date' column to datetime format
    df_plot = df.copy()
    df_plot["timestamp"] = pd.to_datetime(df_plot["timestamp"])

    # Plot multiple columns simultaneously
    ax = df_plot.plot(
        x="timestamp",
        y=[column_name],
        kind="line",
        marker="o",
        linestyle="-",
        markersize=1,
    )

    # Add labels and title
    plt.xlabel("Timestamp")
    plt.ylabel(column_name)
    plt.title(f"{column_name} Plot")
    plt.grid()

    # Format the x-axis to show more detailed timestamps
    ax.xaxis.set_major_locator(
        mdates.HourLocator(interval=1)
    )  # Set the interval to show every day
    ax.xaxis.set_major_formatter(
        mdates.DateFormatter("%Y-%m-%d  %H:%M:%S")
    )  # Format the date as YYYY-MM-DD

    # Rotate x-axis labels for better readability
    plt.xticks(rotation=45)

    # Show the plot
    plt.show()
