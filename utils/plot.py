import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
import tomllib


with open(".streamlit/config.toml", "rb") as f:
    THEME_COLORS = tomllib.load(f)["theme"]


# function to convert hex to rgba
def hex_to_rgba(hex, alpha):
    hex = hex.lstrip("#")
    return f"rgba({int(hex[:2], 16)},{int(hex[2:4], 16)},{int(hex[4:], 16)},{alpha})"


COLOR_HIGHLIGHT = THEME_COLORS["primaryColor"]
COLOR_HIGHLIGHT_HIGH = hex_to_rgba(COLOR_HIGHLIGHT, 0.6)
COLOR_HIGHLIGHT_MID = hex_to_rgba(COLOR_HIGHLIGHT, 0.4)
COLOR_FADED = "rgba(60,60,60,0.25)"
COLOR_SECONDARY = "#0af"


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
                        line=dict(color=COLOR_HIGHLIGHT, width=3),
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
                    line=dict(color=COLOR_FADED, width=2),
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
            marker=dict(color=COLOR_HIGHLIGHT, size=12),
            showlegend=False,
            hoverinfo="skip",
            text=[f"${y_l:,.0f}", f"${y_r:,.0f}"],
            textposition="top left",
            textfont=dict(
                size=25,
                color=COLOR_HIGHLIGHT,
                weight=3,
                shadow="0px 0px 3px white, 0 0 1px white",
            ),
        )
    )

    return traces


def cost_per_month_traces(monthly_data, ycols, ycol_highlight, left, right):
    """
    Generate traces for a cost per month plot.

    Parameters:
    - monthly_data (pandas.DataFrame): The data containing the monthly values.
    - ycols (list): The list of column names to plot.
    - ycol_highlight (str): The column name to highlight.
    - left (int): The left boundary index for starting a sum.
    - right (int): The right boundary index for ending the sum.

    Returns:
    - traces (list): The list of plotly Scatter objects representing the traces.
    """
    hover_template = "<b>Cost per Month</b>: $%{y:,.0f}"

    traces = []
    for column in ycols:
        if column == ycol_highlight:
            # plot from 0 to shade_l
            data_left = monthly_data.loc[monthly_data.index < left]
            data_right = monthly_data.loc[monthly_data.index > right]
            data_middle = monthly_data.loc[
                (monthly_data.index >= left) & (monthly_data.index <= right)
            ]
            for d in [data_left, data_right, data_middle]:
                opacity = 1 if d is data_middle else 0.2
                traces.append(
                    go.Scatter(
                        x=d.index,
                        y=d[column],
                        mode="lines",
                        line=dict(color=COLOR_HIGHLIGHT, width=3),
                        showlegend=False,
                        opacity=opacity,
                        hovertemplate=hover_template,
                        name=column,
                    )
                )

        else:
            traces.append(
                go.Scatter(
                    x=monthly_data.index,
                    y=monthly_data[column],
                    mode="lines",
                    line=dict(color=COLOR_FADED, width=2),
                    showlegend=False,
                    hovertemplate=hover_template,
                    name=column,
                )
            )

    # add maker at left, right
    y_l = monthly_data.loc[monthly_data.index == left, ycol_highlight].values[0]
    y_r = monthly_data.loc[monthly_data.index == right, ycol_highlight].values[
        0
    ]

    traces.append(
        go.Scatter(
            x=[left, right],
            y=[y_l, y_r],
            mode="markers+text",
            marker=dict(color=COLOR_HIGHLIGHT, size=12),
            showlegend=False,
            hoverinfo="skip",
            text=[f"${y_l:,.0f}", f"${y_r:,.0f}"],
            textposition="top center",
            textfont=dict(
                size=25,
                color=COLOR_HIGHLIGHT,
                weight=3,
                shadow="0px 0px 3px white, 0 0 1px white",
            ),
        )
    )

    return traces


def plot_bars(adjusted_tuition_dict: dict, age_group: str):
    """
    Plot a bar chart of the adjusted tuition values.

    Args:
        adjusted_tuition_dict (dict): The dictionary of adjusted tuition values.

    Returns:
        fig (plotly.graph_objects.Figure): The plotly figure object.
    """
    # list of colors
    colors = [
        COLOR_HIGHLIGHT_HIGH if key == age_group else COLOR_HIGHLIGHT_MID
        for key in adjusted_tuition_dict.keys()
    ]

    # side by side bar chart
    fig = go.Figure()
    for i, (key, value) in enumerate(adjusted_tuition_dict.items()):
        fig.add_trace(
            go.Bar(
                x=[key],
                y=[value],
                name=key,
                marker_color=colors[i],
                hoverinfo="skip",
                # bar width
                width=0.9,
            )
        )

    # hide everything except the bars
    fig.update_layout(
        showlegend=False,
        margin=dict(l=0, r=0, t=0, b=0),
        hovermode="closest",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        # no labels
        xaxis=dict(showticklabels=False),
        yaxis=dict(showticklabels=False),
        # no grid
        xaxis_showgrid=False,
        yaxis_showgrid=False,
        # width and height
        width=10,
        height=80,
    )
    return fig


def plot_trend(
    cumulative_data,
    monthly_data,
    columns_included,
    column_highlight,
    left,
    right,
    xcol=None,
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
    data = cumulative_data.copy()
    # make xcol the index
    if xcol:
        data.set_index(xcol, inplace=True)

    # offset data to start at left
    data[columns_included] = (
        data[columns_included] - data.loc[left, columns_included]
    )
    # subplots
    fig = make_subplots(
        rows=2,
        cols=1,
        column_widths=[8],
        row_heights=[8, 4],
        # shared_xaxes=True,
        horizontal_spacing=0.02,
        vertical_spacing=0.1,
        subplot_titles=(
            "Cumulative Cost",
            "Cost per Month",
        ),
    )

    # plot lines in the main plot

    main_traces = sum_lines_traces(
        data, columns_included, column_highlight, left, right, marker_text
    )

    for trace in main_traces:
        fig.add_trace(trace, row=1, col=1)

    # add cost_per_month as subplot

    monthly_traces = cost_per_month_traces(
        monthly_data, columns_included, column_highlight, left, right
    )

    for trace in monthly_traces:
        fig.add_trace(trace, row=2, col=1)

    # add intervals to ticks
    xticks = np.concatenate([np.arange(0, 72, 10), np.array([left, right])])
    # drop duplicates
    xticks = np.unique(xticks).tolist()
    # sort
    xticks.sort()

    xticklabels = [str(x) for x in xticks]
    xticklabels[0] = "0<br><i>months</i>"
    # make left and right bold
    left_index = xticks.index(left)
    right_index = xticks.index(right)
    xticklabels[left_index] = f"<b>{left}</b>"
    xticklabels[right_index] = f"<b>{right}</b>"
    if (left - 1 in xticks) or (left + 1 in xticks):
        xticklabels[left_index] = "<br>" + xticklabels[left_index]
    if (right - 1 in xticks) or (right + 1 in xticks):
        xticklabels[right_index] = "<br>" + xticklabels[right_index]

    # general styling
    fig.update_layout(
        height=800,
        hoverlabel=dict(
            font_size=16,
        ),
        hovermode="x",
        margin=dict(l=0, r=20, t=30, b=60),
    )

    # style subplots
    for d, row in zip([data, monthly_data], [1, 2]):
        min_value = d[columns_included].min().min()
        max_value = d[columns_included].max().max()
        value_delta = max_value - min_value
        fig.update_yaxes(
            row=row,
            col=1,
            range=[
                min_value - 0.05 * value_delta,
                max_value + 0.2 * value_delta,
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
            tickfont=dict(color="gray", size=18),
        )

        fig.update_xaxes(
            row=row,
            col=1,
            showgrid=False,
            ticks="inside",
            tickvals=xticks,
            ticktext=xticklabels,
            tickangle=0,
            tickfont=dict(size=18),
            showline=True,
            linewidth=1,
            linecolor="black",
        )

    return fig


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
