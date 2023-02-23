import matplotlib.pyplot as plt


def lines_bar(df, x, l1, l2, b, x_label, y_label1, y_label2):
    fig = plt.figure(figsize=(10, 5))

    # Create axis objects for the lines and bar chart
    ax1 = fig.add_subplot()
    ax2 = ax1.twinx()

    # Plot the first line
    ax1.plot(df[x], df[l1], color='red', label=l1)

    # Plot the second line
    ax1.plot(df[x], df[l2],
             color='green', label=l2)

    # Plot the bar chart on the second axis
    ax2.bar(df[x], df[b],
            color='blue', alpha=0.5, label=b)

    # Set labels and legend
    ax1.set_xlabel(x_label)
    ax1.set_ylabel(y_label1)
    ax2.set_ylabel(y_label2)
    ax1.legend(loc='upper left')
    ax2.legend(loc='upper right')

    # Rotate the x-axis labels by 90 degrees
    ax1.set_xticklabels(df[x], rotation=90)

    # Show the plot
    plt.tight_layout()
    return plt
