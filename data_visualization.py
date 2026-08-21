import base64
import datetime
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import re
import textwrap

import plotly.io as pio
pio.templates.default = 'plotly_white'
pio.templates['plotly_white'].layout.font.family = 'Montserrat, sans-serif'

"""
Data visualizations for SolarWAVE Action.

Author: Jenny Folkesson: jenny@solarwaveaction.org
"""


SOLARWAVE_BLUE = '#1775c9'


def add_logo(logo_path, fig, x=0.99, y=1.1):
    """
    Add logo to the top-right corner of a figure.

    x and y are paper coordinates: 0–1 spans the plot area, and y > 1
    goes into the top margin. Increase the figure's top margin
    (e.g. margin=dict(t=80)) if the logo or text is clipped.

    :param str logo_path: Path to logo image, or a public URL (preferred for blog export)
    :param go.Figure fig: Plotly figure
    :param float x: Right edge of the logo in paper coordinates (default 0.99)
    :param float y: Top edge of the logo in paper coordinates (default 1.10)
    :return go.Figure fig: Figure with logo and copyright added
    """
    if logo_path.startswith("http"):
        source = logo_path
    else:
        with open(logo_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode("utf-8")
        source = f"data:image/png;base64,{encoded_string}"

    sizex, sizey = 0.144, 0.108
    fig.layout.images = [dict(
        source=source,
        xref="paper",
        yref="paper",
        x=x,
        y=y,
        sizex=sizex,
        sizey=sizey,
        xanchor="right",
        yanchor="top",
    )]
    return fig


def write_html_with_fonts(fig, write_path):
    html = fig.to_html(full_html=True,
                       include_plotlyjs='cdn',
                       config={"responsive": True, "displaylogo": False})
    font_link = (
              '<link rel="preconnect" href="https://fonts.googleapis.com">\n'
              '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
              '<link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600&display=swap" rel="stylesheet">\n')
    # Re-layout after fonts load — Plotly renders before async Google Fonts arrive,
    # so without this the fallback sans-serif is used permanently.
    font_ready_script = (
        '<script>\n'
        'document.fonts.ready.then(function() {\n'
        '  var gd = document.querySelector(".plotly-graph-div");\n'
        '  if (gd) Plotly.relayout(gd, {"font.family": "Montserrat, sans-serif"});\n'
        '});\n'
        '</script>\n')
    html = html.replace('</head>', font_link + '</head>', 1)
    html = html.replace('</body>', font_ready_script + '</body>', 1)
    with open(write_path, 'w') as f:
        f.write(html)


def commercial_capacity_per_year(df_total,
                                 date_type='App Received Date',
                                 y_range=None,
                                 layout_size=None,
                                 logo_path=None):
    """
    Bar graph showing added capacity each year.

    :param pd.DataFrame df_total: DGStats data for all sectors of interest
    :param str date_type: One of 'App Received Date', 'App Approved Date'
    :param int/None y_range: Set graph Y range
    :param list/None layout_size: Size of graph (width, height). None sets autosize to True.
    :param str logo_path: Optional path or URL to logo image
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
    hover_text = ("System Size: " + df['System Size DC'].astype(str) + " MW" +
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
                  annotation_text="NEM Cutoff",
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
    fig.add_annotation(
        text='How AB 2143 Derailed Commercial Solar Adoption in Santa Cruz County',
        xref='paper',
        yref='paper',
        x=0.05,
        y=1.07,
        showarrow=False,
        font=dict(size=16),
        xanchor='left',
        yanchor='top',
    )
    fig.add_annotation(
        text="Commercial and industrial system capacity (MW) added quarterly in Santa Cruz County in the years 2021-25.<br>Data Source: California DG Statistics",
        xref="paper",
        yref="paper",
        x=0,
        y=-0.4,
        showarrow=False,
        font=dict(size=11),
        xanchor="left",
        yanchor="bottom",
        align="left",
    )
    fig.update_layout(
        barmode='stack',
        legend={'title': 'Tariff'},
        yaxis_title='System Size DC (MW)',
        xaxis_title=xtitle,
        margin=dict(l=40, r=40, t=100, b=180),
        autosize=True,
        height=600,
        font=dict(size=10),
        showlegend=False,
        font_family="Montserrat, sans-serif",
        title_font_family="Montserrat, sans-serif",
    )

    if logo_path is not None:
        fig = add_logo(logo_path, fig, y=1.25)
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
        margin=dict(l=40, r=20, t=20, b=20),
        autosize=True,
        # width=800,
        # height=500,
        font=dict(size=12),
        legend={'title': 'Source, Tariff'},
        yaxis_title='Number of Applications',
        xaxis_title='Application Year',
    )
    return fig


def application_time_bargraph(df):
    """
    Bar plot of DGStats application times.

    :param pd.DataFrame df: DGstats data
    :return go.Figure fig: Figure handle
    """

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

    fig.update_layout(
        barmode='group',
        margin=dict(l=40, r=20, t=20, b=20),
        autosize=True,
        # width=800,
        # height=400,
        font=dict(size=12),
        yaxis_title='Application Time (Days)',
        xaxis_title='Approved Year',
        legend={'title': 'Time Interval'},
    )
    fig.update_xaxes(
        dtick="Y",
        range=["2020-11-15", "2026-01-10"],
        tickangle=0,
    )
    return fig


def electricity_rates_scatter(df, max_year=None):
    """
    Scatter plot of bundled electricity rates over years.
    Compiling data and adjustment for inflation happens in
    data_analysis.compile_electricity_rates.

    :param pd.DataFrame df: US, CA, and PGE electricity rates
    :param int max_year: Maximum year on x-axis
    :return go.Figure fig: Figure data handle
    """
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
        margin=dict(l=40, r=20, t=20, b=20),
        title_x=0.5,
        yaxis_title='Average Electricity Price (¢/kWh)',
        xaxis_title='Year',
        autosize=True,
        # width=800,
        # height=500,
        font=dict(size=12),
        xaxis=dict(
            tickmode='linear',
            tick0=2010,
            dtick=2,
            range=[2010, df['Year'].max()],
        ),
        hovermode="x unified",
    )
    if max_year is None:
        max_year = df['Year'].max()
    fig.update_xaxes(
        dtick=2,  # every 2 years, no datetime formatting needed
        range=[2010, max_year],
    )
    # fig.update_yaxes(
    #     range=[0, 37],
    # )
    fig.update_traces(hovertemplate=None)
    return fig


def what_didnt_kill_rooftop_solar_graph(df, dates, max_date=None, logo_path=None, caption_text=None):
    """
    Visualization of the underlying rooftop solar applications with one of Borenstein's
    Before/After bar sets superimposed, along with NBT decision and application dates.

    :param pd.DataFrame df: Dataframe containing solar applications from DGStats
    :param list[dict] dates: Before/After time intervals [{x0, x1}, {x0, x1}]
    :param str max_date: The most recent date to be used from df
    :param str logo_path: Optional path or URL to logo image
    :param str caption_text: Optional caption text
    :return go.Figure fig: Resulting figure
    """
    df_system = df.copy()
    df_system['App Days'] = (df_system['App Approved Date'] -
                             df_system['App Received Date']).dt.days
    df_system = df_system[df_system['Customer Sector'] == 'Residential']
    if max_date is not None:
        df_system = df_system[(df_system['App Received Date'] <= max_date)]

    df = df_system[(df_system['NEM Tariff'] == '1.0') | (df_system['NEM Tariff'] == '2.0')]
    df = df[['App Received Date', 'System Size DC', 'App Days']]
    df = df.set_index('App Received Date').rename_axis(None)
    df['Nbr Installations'] = 1
    df = df.resample("ME").agg({'System Size DC': 'sum', 'Nbr Installations': 'count'})
    df['Month'] = df.index
    # Plot NEM applications
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df['Month'],
        y=df['System Size DC'],
        hovertext=df['Month'].dt.strftime('%B %Y'),
        hovertemplate='%{hovertext}<br>System Size: %{y:.1f} kW<extra>NEM</extra>',
        marker_color='rgb(255,217,47)',
        offsetgroup=0,
        xperiod="M1",
        name='NEM Applications',
    ))

    df = df_system[df_system['NEM Tariff'] == 'NBT']
    df = df[['App Received Date', 'System Size DC', 'App Days']]
    df = df.set_index('App Received Date').rename_axis(None)
    df['Nbr Installations'] = 1
    df = df.resample("ME").agg({'System Size DC': 'sum', 'Nbr Installations': 'count'})
    df['Month'] = df.index
    # Plot NBT applications
    fig.add_trace(go.Bar(
        x=df['Month'],
        y=df['System Size DC'],
        hovertext=df['Month'].dt.strftime('%B %Y'),
        hovertemplate='%{hovertext}<br>System Size: %{y:.1f} kW<extra>NBT</extra>',
        marker_color='rgb(230,171,2)',
        offsetgroup=0,
        xperiod="M1",
        name='NBT Applications',
    ))
    # Draw dashed lines for dates: NBT decision and NEM cutoff
    fig.add_vline(x=datetime.datetime(2022, 12, 1).timestamp() * 1000,
                  line_width=2, line_dash="dash", line_color="red",
                  )
    fig.add_vline(x=datetime.datetime(2023, 4, 15).timestamp() * 1000,
                  line_width=2, line_dash="dash", line_color="green",
                  )
    # Add dashed lines to legend
    fig.add_trace(go.Scatter(
        x=[None], y=[None], mode='lines',
        line=dict(color='green', width=2, dash='dash'),
        name='NEM Cutoff',
    ))
    fig.add_trace(go.Scatter(
        x=[None], y=[None], mode='lines',
        line=dict(color='red', width=2, dash='dash'),
        name='NBT Decision',
    ))
    # Draw Before interval: transparent rectangle in red
    fig.add_vrect(dates[0]['x0'], dates[0]['x1'],
                  annotation_text="Before",
                  annotation_position="top left",
                  annotation=dict(font_size=12),
                  fillcolor="red",
                  opacity=0.15,
                  line_width=0)
    # Draw After inteval: transparent rectangle in green
    fig.add_vrect(dates[1]['x0'], dates[1]['x1'],
                  annotation_text="After",
                  annotation_position="top left",
                  annotation=dict(font_size=12),
                  fillcolor="green",
                  opacity=0.15,
                  line_width=0,
                  )

    fig.update_xaxes(
        dtick="M12",
        tickformat="%Y",
        range=["2019-01-01", max_date],
        tickangle=0,
    )
    # Title
    fig.add_annotation(
        text='How Date Selection Distorts Rooftop Solar Market Signals',
        xref='paper',
        yref='paper',
        x=0.05,
        y=1.07,
        showarrow=False,
        font=dict(size=16),
        xanchor='left',
        yanchor='top',
    )
    # Caption
    if caption_text is not None:
        fig.add_annotation(
            text=caption_text,
            xref="paper",
            yref="paper",
            x=0,
            y=-0.4,
            showarrow=False,
            font=dict(size=11),
            xanchor="left",
            yanchor="bottom",
            align="left",
        )
    fig.update_layout(
        barmode='stack',
        margin=dict(l=40, r=40, t=100, b=180),
        autosize=True,
        height=600,
        font=dict(size=10),
        font_family="Montserrat, sans-serif",
        title_font_family="Montserrat, sans-serif",
        yaxis_title='System Size DC (MW)',
        xaxis_title='Application Received Date',
        legend={'title': 'Dates & Applications'},
    )

    if logo_path is not None:
        fig = add_logo(logo_path, fig, x=1.15, y=1.25)

    return fig


def cost_shift_bargraph(logo_path=None):
    """
    Visually compare different cost shift measures and reference them to wildfire spending
    and earnings.
    Sources: PAO, CPUC, Borenstein (2024), M.Cubed (2024), FERC Form 1 filings
    Form 1 filings from PUDL https://data.catalyst.coop/preview/pudl/out_ferc1__yearly_income_statements_sched114?return_q=name%3Aferc1&filters=%255B%257B%2522fieldName%2522%253A%2522report_year%2522%252C%2522fieldType%2522%253A%2522number%2522%252C%2522operation%2522%253A%2522equals%2522%252C%2522value%2522%253A2024%257D%252C%257B%2522fieldName%2522%253A%2522income_type%2522%252C%2522fieldType%2522%253A%2522text%2522%252C%2522operation%2522%253A%2522contains%2522%252C%2522value%2522%253A%2522net_income_loss%2522%257D%255D
    :param str logo_path: Optional path or URL to logo image
    :return go.Figure fig: Resulting bar graph
    """
    MUTED = 'rgb(190, 185, 205)'  # other estimate bars, stepped back

    cost_method = ['PAO', 'CPUC', 'Borenstein', 'SolarWAVE', 'M.Cubed']
    cost_billions = [8.455, 7.0, 3.856, 2.547, -1.5]
    left_labels = ['$8.5B', '$7.0B', '$3.8B', '$2.5B', '–$1.5B']
    bar_colors = [MUTED, MUTED, MUTED, SOLARWAVE_BLUE, MUTED]

    fig = make_subplots(rows=1, cols=2, column_widths=[5/8, 3/8])

    fig.add_trace(
        go.Bar(
            x=cost_method,
            y=cost_billions,
            text=left_labels,
            textposition='outside',
            textfont=dict(size=11),
            hovertemplate='Cost shift method: %{x}<br>Estimate: $%{y:.1f} billion<extra></extra>',
            marker=dict(
                color=bar_colors,
                # hatch signals these are modeled estimates, not actuals
                pattern=dict(shape='/', fgcolor='rgba(0,0,0,0.2)', solidity=0.3),
            ),
        ),
        row=1, col=1,
    )
    fig.update_xaxes(
        title_text='2024 Cost Shift Estimates<br><sup>modeled estimates, methodologies vary</sup>',
        row=1, col=1,
    )

    cost_category = ['2024<br>Wildfire<br>Spending', '2024<br>Net<br>Profits', '2025<br>Net<br>Profits']
    amount_billions = [8.985, 5.384, 8.675]
    right_labels = ['$9.0B', '$5.4B', '$8.7B']

    fig.add_trace(
        go.Bar(
            x=cost_category,
            y=amount_billions,
            text=right_labels,
            textposition='outside',
            textfont=dict(size=11),
            hovertemplate='Category: %{x}<br>Amount: $%{y:.1f} billion<extra></extra>',
            marker_color='rgb(117,112,179)',
        ),
        row=1, col=2,
    )
    fig.update_xaxes(
        title_text='IOU Wildfire Spending and Profits<br><sup>reported figures</sup>',
        row=1, col=2,
    )

    fig.update_yaxes(range=[-2.8, 10.5])

    # SolarWAVE estimate is a ceiling — signal that in the chart itself
    fig.add_annotation(
        x='SolarWAVE',
        y=2.547,
        text='↓ likely lower',
        showarrow=False,
        yshift=45,
        font=dict(size=10, color=SOLARWAVE_BLUE),
        xref='x',
        yref='y',
    )
    fig.add_annotation(
        text="Left: Comparison of different 2024 cost shift estimates from PAO, CPUC, Borenstein, SolarWAVE Action (blue) and M.Cubed.<br>Right: 2024 wildfire spending and 2024-25 net profits in total for the three IOUs PG&E, SCE and SDG&E for comparison.<br>Data Source: PAO, CPUC, Borenstein (2024), M.Cubed (2024), FERC Form 1 filings via PUDL.",
        xref="paper",
        yref="paper",
        x=0,
        y=-0.6,
        showarrow=False,
        font=dict(size=11),
        xanchor="left",
        yanchor="bottom",
        align="left",
    )
    fig.add_annotation(
        text='Corrected Solar Cost Shift Dwarfed by Utility Wildfire Spending and Profits',
        xref='paper',
        yref='paper',
        x=0.05,
        y=1.07,
        showarrow=False,
        font=dict(size=16),
        xanchor='left',
        yanchor='top',
    )
    fig.update_layout(
        margin=dict(l=40, r=40, t=100, b=200),
        autosize=True,
        height=600,
        font=dict(size=10),
        yaxis_title='$ Billion US Dollars',
        showlegend=False,
        font_family="Montserrat, sans-serif",
        title_font_family="Montserrat, sans-serif",
    )

    if logo_path is not None:
        fig = add_logo(logo_path, fig, y=1.25)

    return fig
