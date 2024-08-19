import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
import pandas as pd

COLOR_HIGHLIGHT = "rgba(65,40,200,1)"


def sum_lines_traces(
    data, ycols, ycol_highlight, left, right, marker_text=True
):
    """
    Generate traces for a cumulative sum plot.

    Parameters:
    - data (pandas.DataFrame): The data containing the individual values.
    - ycols (list): The list of column names to plot.
    - ycol_highlight (str): The column name to highlight.
    - left (int): The left boundary index for starting a sum.
    - right (int): The right boundary index for ending the sum.
    - marker_text (bool, optional): Whether to include marker text. Defaults to True.

    Returns:
    - traces (list): The list of plotly Scatter objects representing the traces.
    """
    hover_template = "<b>Cumulative Cost</b>: $%{y:,.0f}"

    traces = []
    for column in ycols:
        if column == ycol_highlight:
            # plot from 0 to shade_l
            data_left = data.loc[data.index < left]
            data_right = data.loc[data.index > right]
            data_middle = data.loc[(data.index >= left) & (data.index <= right)]
            for d in [data_left, data_right, data_middle]:
                opacity = 1 if d is data_middle else 0.2
                traces.append(
                    go.Scatter(
                        x=d.index,
                        y=d[column],
                        mode="lines",
                        line=dict(color=COLOR_HIGHLIGHT, width=2),
                        showlegend=False,
                        opacity=opacity,
                        hovertemplate=hover_template,
                        name=column,
                    )
                )

        else:
            traces.append(
                go.Scatter(
                    x=data.index,
                    y=data[column],
                    mode="lines",
                    line=dict(color="rgba(60,60,60,0.25)", width=2),
                    showlegend=False,
                    hovertemplate=hover_template,
                    name=column,
                )
            )

    # add maker at left, right
    y_l = data.loc[data.index == left, ycol_highlight].values[0]
    y_r = data.loc[data.index == right, ycol_highlight].values[0]

    traces.append(
        go.Scatter(
            x=[left, right],
            y=[y_l, y_r],
            mode="markers+text",
            marker=dict(color=COLOR_HIGHLIGHT, size=6),
            showlegend=False,
            hoverinfo="skip",
            text=[f"${y_l:,.0f}", f"${y_r:,.0f}"],
            textposition="top center",
            textfont=dict(
                size=16,
                color=COLOR_HIGHLIGHT,
                weight=3,
                shadow="0px 0px 3px white, 0 0 1px white",
            ),
        )
    )

    return traces


def plot_trend(
    data,
    xcol,
    columns_included,
    column_highlight,
    left,
    right,
    marker_text=True,
):
    """
    Plot the trend of specified columns in a dataset.

    Args:
        data (DataFrame): The dataset to plot.
        xcol (str): The column to use as the x-axis.
        columns_included (list): The columns to include in the plot.
        column_highlight (str): The column to highlight in the plot.
        left (int): The left offset for the data.
        right (int): The right offset for the data.
        marker_text (bool, optional): Whether to display marker text. Defaults to True.

    Returns:
        None
    """
    # create a copy of data to avoid modifying the original
    data = data.copy()
    # make xcol the index
    data.set_index(xcol, inplace=True)

    # offset data to start at left
    data[columns_included] = (
        data[columns_included] - data.loc[left, columns_included]
    )
    # subplots
    fig = make_subplots(
        rows=1,
        cols=1,
        column_widths=[8],
        row_heights=[8],
        shared_yaxes=True,
        horizontal_spacing=0.02,
    )

    # plot lines in the main plot

    main_traces = sum_lines_traces(
        data, columns_included, column_highlight, left, right, marker_text
    )

    for trace in main_traces:
        fig.add_trace(trace, row=1, col=1)

    # update layout
    fig.update_layout(
        font=dict(size=14),
        width=800,
        height=600,
        # ymin
        yaxis=dict(
            range=[
                data[columns_included].min().min(),
                data[columns_included].max().max(),
            ],
            showgrid=True,
            tickformat="$~s",
            gridcolor="lightgray",
            gridwidth=1,
            griddash="dash",
            zeroline=False,
            showline=False,
            showticklabels=True,
            tickmode="array",
            ticklabelposition="inside top",
            tickfont=dict(color="gray", size=15),
        ),
        xaxis=dict(
            showgrid=False,
            ticks="inside",
            range=[-10, 72],
            tickvals=[0, 10, 20, 30, 40, 50, 60, 70],
            ticktext=[
                "0 <i>months</i>",
                "10",
                "20",
                "30",
                "40",
                "50",
                "60",
                "70",
            ],
            tickangle=0,
            tickfont=dict(size=14),
            showline=True,
            linewidth=1,
            linecolor="black",
        ),
        hovermode="x",
        plot_bgcolor="white",
        margin=dict(l=0, r=20, t=30, b=60),
    )

    fig.show()


def _vertical_traces(data, ycol_highlight, left, right):
    """Deprecated"""

    traces = []
    # plot from 0 to shade_l
    data_left = data.loc[data.index < left, [ycol_highlight]]
    data_right = data.loc[data.index > right, [ycol_highlight]]
    data_middle = data.loc[
        (data.index >= left) & (data.index <= right), [ycol_highlight]
    ]
    for d in [data_left, data_right, data_middle]:
        opacity = 1 if d is data_middle else 0.2
        traces.append(
            go.Scatter(
                x=[0] * len(d),
                y=d[ycol_highlight],
                mode="lines",
                line=dict(color="rgba(65,40,200,1)"),
                showlegend=False,
                opacity=opacity,
                hoverinfo="skip",
            )
        )

    # add marker at left, right
    y_l = data_middle[ycol_highlight].min()
    y_r = data_middle[ycol_highlight].max()

    traces.append(
        go.Scatter(
            x=[0, 0],
            y=[y_l, y_r],
            mode="markers",
            marker=dict(color="rgba(95,40,200,1)", size=6),
            showlegend=False,
            hovertemplate="<br><b>Cumulative Cost</b>: $%{y:,.0f}",
            name=ycol_highlight,
        )
    )

    traces.append(
        go.Scatter(
            x=[1],
            y=[y_r],
            text=[f"${y_r - y_l:,.0f}"],
            textfont=dict(size=16, color="rgba(95,40,200,1)", weight="bold"),
            textposition="middle right",
            hoverinfo="skip",
            mode="text",
            showlegend=False,
        )
    )

    return traces
