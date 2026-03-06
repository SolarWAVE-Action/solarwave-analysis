import datetime
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

"""
Data visualizations for SolarWAVE Action.

Author: Jenny Folkesson: jenny@solarwaveaction.org
"""


def commercial_capacity_per_year(df_total, date_type='App Received Date', y_range=None):
    """
    Bar graph showing added capacity each year.

    :param pd.DataFrame df_total: DGStats data for all sectors of interest
    :param str date_type: One of 'App Received Date', 'App Approved Date'
    :param int/None y_range: Set graph Y range
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
    hover_text = ("System Size: " + df['System Size DC'].astype(str) + " kW" +
                  "<br> Nbr Applications: " + df['Nbr Applications'].astype(str))
    fig.add_trace(go.Bar(
        x=df['Quarter'],
        y=df['System Size DC'],
        offsetgroup=0,
        marker_color='rgb(102,194,165)',
        hovertext=hover_text,
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
    hover_text = ("System Size: " + df['System Size DC'].astype(str) + " kW" +
                  "<br> Nbr Applications: " + df['Nbr Applications'].astype(str))
    fig.add_trace(go.Bar(
        x=df['Quarter'],
        y=df['System Size DC'],
        offsetgroup=0,
        marker_color='rgb(252,141,98)',
        hovertext=hover_text,
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
    if isinstance(y_range, int):
        fig.update_yaxes(
            range=[0, y_range],
        )
    return fig


def dgstats_vs_pge_bargraph(df_total, date_type='App Received Date'):
    """
    Compare nonresidential application volume received directly from PG&E to
    what was visible at DGStats at the time.

    :param pd.DataFrame df_total: All collected DGStats applications from the last 5 years
    :param str date_type: Available DGStats dates (App Received Date, App Complete Date,
        App Approved Date)
    :return go.Figure fig: Resulting bar graph
    """
    # We received this data in April 2025, so we need to remove more recent dates
    df_date = df_total[df_total['App Approved Date'] < '2025-05-01']
    # This is nonresidential PG&E data
    df_date = df_date[df_date['IOU'] == 'PGE']
    df_date = df_date[df_date['Customer Sector'] != 'Residential']
    df_date = df_date[df_date['Customer Sector'] != 'Not available']
    # NEM
    df = df_date[(df_date['NEM Tariff'] == '1.0') |
                 (df_date['NEM Tariff'] == '2.0')]
    df = df[[date_type, 'System Size DC']]
    df['Nbr Applications'] = 1
    df = df.set_index(date_type).rename_axis(None)
    df = df.groupby(df.index.year).sum()

    fig = make_subplots(rows=1, cols=2, column_widths=[0.25, 0.75])
    y_vals = [3100]
    fig.add_trace(
        go.Bar(x=[2022], y=y_vals,
               name='PGE NEM',
               # text=y_vals,
               marker_color='rgb(141,160,203)'),
        row=1, col=1,
    )
    y_vals = [df.loc[2022, 'Nbr Applications']]
    fig.add_trace(
        go.Bar(x=[2022], y=y_vals,
               name='DGSt NEM',
               # text=y_vals,
               marker_color='rgb(166,216,84)'),
        row=1, col=1,
    )

    df = df_date[(df_date['NEM Tariff'] == 'NBT')]
    df = df[[date_type, 'System Size DC']]
    df['Nbr Applications'] = 1
    df = df.set_index(date_type).rename_axis(None)
    df = df.groupby(df.index.year).sum()
    # Numbers received directly from PG&E
    y_vals = [359, 438, 190]
    fig.add_trace(
        go.Bar(x=[2023, 2024, 2025], y=y_vals,
               name='PGE NBT',
               # text=y_vals,
               marker_color='rgb(117,112,179)'),
        row=1, col=2,
    )
    y_vals = df['Nbr Applications']
    fig.add_trace(
        go.Bar(x=df.index, y=y_vals,
               name='DGSt NBT',
               # text=y_vals,
               marker_color='rgb(102,166,30)'),
        row=1, col=2,
    )
    fig.update_yaxes(
        range=[0, 3110],
    )
    fig.update_xaxes(title_text='Application Year', row=1, col=2)
    fig.update_layout(
        barmode='group',
        autosize=False,
        width=800,
        height=500,
        font=dict(size=12),
        legend={'title': 'Source, Tariff'},
        yaxis_title='Number of Applications',
        xaxis_title='Application Year',
    )
    return fig


def application_time_bargraph(df):

    df_system = df.copy()

    df_system['Received-Complete'] = (
        (df_system['App Complete Date'] - df_system['App Received Date']).dt.days)
    df_system['Complete-Approved'] = (
        (df_system['App Approved Date'] - df_system['App Complete Date']).dt.days)

    df = df_system[['App Approved Date',
                    'System Size DC',
                    'Received-Complete',
                    'Complete-Approved']]
    df = df.set_index('App Approved Date').rename_axis(None)

    df = df.resample("YE").agg({'System Size DC': 'sum',
                                'Received-Complete': 'median',
                                'Complete-Approved': 'median'})
    df['Year'] = df.index.year
    df = df[df['Year'] >= 2021]
    hover_text = ("Year: " + df['Year'].astype(str) +
                  "<br> Received-Complete days: " + df['Received-Complete'].astype(str))

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df['Year'],
        y=df['Received-Complete'],
        marker_color='rgb(117,112,179)',
        hovertext=hover_text,
        offsetgroup=0,
        name='Rec-Comp',
    ))
    hover_text = ("Year: " + df['Year'].astype(str) +
                  "<br> Complete-Approved days: " + df['Complete-Approved'].astype(str))
    fig.add_trace(go.Bar(
        x=df['Year'],
        y=df['Complete-Approved'],
        marker_color='rgb(141,160,203)',
        hovertext=hover_text,
        offsetgroup=0,
        name='Comp-Appr',
    ))
    xtitle = 'Application Year'
    if date_type == 'App Approved Date':
        xtitle = 'Approved Year'

    fig.update_layout(
        barmode='group',
        autosize=False,
        width=800,
        height=400,
        font=dict(size=12),
        yaxis_title='Application Time (Days)',
        xaxis_title=xtitle,
        legend={'title': 'Time Interval'},
    )
    fig.update_xaxes(
        dtick="Y",
        range=["2020-11-15", "2026-01-10"],
        tickangle=0,
    )
    return fig


def electricity_rates_scatter(df):
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=df['Year'],
            y=df['US'],
            name='US',
            mode='lines',
            line=dict(width=2, color='orange'),
        ),
    )
    fig.add_trace(
        go.Scatter(
            x=df['Year'],
            y=df['CA'],
            name='CA',
            mode='lines',
            line=dict(width=2, color='purple'),
        ),
    )
    fig.add_trace(
        go.Scatter(
            x=df['Year'],
            y=df['PGE'],
            name='PGE',
            mode='lines',
            line=dict(width=2, color='blue'),
        ),
    )

    fig.update_layout(
        title_x=0.5,
        yaxis_title='Average Electricity Price (¢/kWh)',
        xaxis_title='Year',
        width=800,
        height=500,
        font=dict(size=12),
        xaxis=dict(
            tickmode='linear',
            tick0=2010,
            dtick=2,
            range=[2010, 2024],
        ),
        hovermode="x unified",
    )
    fig.update_xaxes(
        dtick=2,  # every 2 years, no datetime formatting needed
        range=[2010, 2024],
    )
    fig.update_yaxes(
        range=[0, 37],
    )
    fig.update_traces(hovertemplate=None)
    return fig

