"""
Reusable Plotly chart functions for the PulseIQ dashboard.
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def bar_chart(df: pd.DataFrame, x: str, y: str, title: str = "", color: str = "#1f77b4") -> go.Figure:
    """Simple bar chart with a single colour."""
    fig = px.bar(df, x=x, y=y, title=title)
    fig.update_traces(marker_color=color)
    return fig


def line_chart(df: pd.DataFrame, x: str, y: str, title: str = "") -> go.Figure:
    """Simple line chart with markers."""
    fig = px.line(df, x=x, y=y, title=title, markers=True)
    fig.update_traces(line_color="#1f77b4")
    return fig


def score_scatter(df: pd.DataFrame, x: str, y: str, color: str, title: str = "") -> go.Figure:
    """Scatter plot coloured by a boolean or categorical column."""
    fig = px.scatter(
        df, x=x, y=y, color=color, title=title,
        color_discrete_map={True: "#d62728", False: "#2ca02c"},
    )
    return fig
