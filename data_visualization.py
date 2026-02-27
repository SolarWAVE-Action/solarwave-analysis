import datetime
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

"""
Data visualizations for SolarWAVE Action.

Author: Jenny Folkesson: jenny@solarwaveaction.org
"""


def commercial_capacity_per_year(df_total, date_type='App Received Date'):
    """
    Bar graph showing added capacity each year.

    :param pd.DataFrame df_total: DGStats data for all sectors of interest
    :param str date_type: One of 'App Received Date', 'App Approved Date'
    :return go.Figure fig: Plotly bar graph
    """

    fig = go.Figure()

    df = df_total[(df_total['NEM Tariff'] == '1.0') |
                 (df_total['NEM Tariff'] == '2.0')]

    df = df[[date_type, 'System Size DC']]
    df['Nbr Applications'] = 1
    df = df.set_index(date_type).rename_axis(None)
    df = df.resample("QE").agg({'System Size DC': 'sum', 'Nbr Applications': 'sum'})
    df['NEM Tariff'] = 'NEM ≤ 2.0'

    df['Quarter'] = df.index
    hover_text = ("Quarter: " + df['Quarter'].astype(str) +
                  "<br> System Size: " + df['System Size DC'].astype(str) + " kW" +
                  "<br> Nbr Applications: " + df['Nbr Applications'].astype(str))
    fig.add_trace(go.Bar(
        x=df['Quarter'],
        y=df['System Size DC'],
        offsetgroup=0,
        marker_color='rgb(102,194,165)',
        text=hover_text,
        hoverinfo='text',
        name='NEM',
        xperiod="M3",
        xperiodalignment="middle",
    ))

    df = df_total[(df_total['NEM Tariff'] == 'NBT')]
    df = df[[date_type, 'System Size DC']]
    df['Nbr Applications'] = 1
    df = df.set_index(date_type).rename_axis(None)
    df = df.resample("QE").agg({'System Size DC': 'sum', 'Nbr Applications': 'sum'})
    df['NEM Tariff'] = 'NBT'

    df['Quarter'] = df.index
    hover_text = ("Quarter: " + df['Quarter'].astype(str) +
                  "<br> System Size: " + df['System Size DC'].astype(str) + " kW" +
                  "<br> Nbr Applications: " + df['Nbr Applications'].astype(str))
    fig.add_trace(go.Bar(
        x=df['Quarter'],
        y=df['System Size DC'],
        offsetgroup=0,
        marker_color='rgb(252,141,98)',
        text=hover_text,
        hoverinfo='text',
        name='NBT',
        xperiod="M3",
        xperiodalignment="middle",
    ))

    fig.add_vline(x=datetime.datetime(2023, 4, 15).timestamp() * 1000,
                  line_width=2, line_dash="dash", line_color="blue",
                  annotation_text="NBT",
                  annotation_position="top right",
                  annotation_font_size=12,
                  )

    fig.add_vline(x=datetime.datetime(2024, 1, 1).timestamp() * 1000,
                  line_width=2, line_dash="dash", line_color="red",
                  annotation_text="AB 2143",
                  annotation_position="top right",
                  annotation_font_size=12,
                  )

    xtitle = 'Application Received Quarter'
    if date_type == 'App Approved Date':
        xtitle = 'Application Approved Quarter'

    fig.update_layout(
        barmode='stack',
        autosize=False,
        width=800,
        height=500,
        font=dict(size=12),
        legend={'title': 'Tariff'},
        yaxis_title='System Size DC (kW)',
        xaxis_title=xtitle,
    )
    fig.update_xaxes(
        dtick="M3",
        tickformat="Q%q<br>'%y",
        range=["2020-12-25", "2025-10-10"],
        tickangle=0,
    )
    fig.update_yaxes(
        range=[0, 1800],
    )
    return fig
