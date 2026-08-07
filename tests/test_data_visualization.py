import pandas as pd

from data_visualization import (
    application_time_bargraph,
    commercial_capacity_per_year,
    cost_shift_bargraph,
    dgstats_vs_pge_bargraph,
    electricity_rates_scatter,
    what_didnt_kill_rooftop_solar_graph,
)


def _build_visualization_df():
    return pd.DataFrame(
        {
            "NEM Tariff": ["1.0", "2.0", "NBT", "NBT"],
            "App Received Date": pd.to_datetime(
                ["2023-01-10", "2023-02-15", "2023-05-01", "2023-06-01"]
            ),
            "App Approved Date": pd.to_datetime(
                ["2023-01-15", "2023-02-20", "2023-05-05", "2023-06-05"]
            ),
            "System Size DC": [10, 15, 20, 30],
        }
    )


def test_commercial_capacity_per_year_builds_expected_traces():
    df = _build_visualization_df()

    fig = commercial_capacity_per_year(df)

    assert len(fig.data) == 2
    assert fig.data[0].name == "NEM"
    assert fig.data[1].name == "NBT"
    assert fig.layout.barmode == "stack"
    assert fig.layout.xaxis.title.text == "Application Received Quarter"
    assert len(fig.layout.shapes) == 2
    assert len(fig.layout.annotations) == 2
    assert [annotation.text for annotation in fig.layout.annotations] == ["NEM Cutoff", "AB 2143"]

    # NEM traces aggregate 1.0 and 2.0 rows in Q1 2023.
    nem_quarterly_capacity = dict(zip(fig.data[0].x, fig.data[0].y))
    assert nem_quarterly_capacity[pd.Timestamp("2023-03-31")] == 25

    # NBT traces aggregate both NBT rows in Q2 2023.
    nbt_quarterly_capacity = dict(zip(fig.data[1].x, fig.data[1].y))
    assert nbt_quarterly_capacity[pd.Timestamp("2023-06-30")] == 50


def test_commercial_capacity_per_year_approved_date_updates_xaxis_title():
    df = _build_visualization_df()

    fig = commercial_capacity_per_year(df, date_type="App Approved Date")

    assert fig.layout.xaxis.title.text == "Application Approved Quarter"


def test_dgstats_vs_pge_bargraph_returns_four_traces():
    df = pd.DataFrame({
        "App Approved Date": pd.to_datetime(["2022-03-01", "2022-06-01", "2023-07-01", "2024-07-01"]),
        "App Received Date": pd.to_datetime(["2022-01-01", "2022-02-01", "2023-01-01", "2024-01-01"]),
        "IOU": ["PGE", "PGE", "PGE", "PGE"],
        "Customer Sector": ["Commercial", "Commercial", "Commercial", "Commercial"],
        "NEM Tariff": ["1.0", "2.0", "NBT", "NBT"],
        "System Size DC": [100, 200, 300, 400],
    })

    fig = dgstats_vs_pge_bargraph(df)

    assert len(fig.data) == 4
    trace_names = [t.name for t in fig.data]
    assert "PGE NEM" in trace_names
    assert "DGSt NEM" in trace_names
    assert "PGE NBT" in trace_names
    assert "DGSt NBT" in trace_names


def test_application_time_bargraph_has_two_traces():
    df = pd.DataFrame({
        "App Approved Date": pd.to_datetime(["2021-06-01", "2022-06-01", "2023-06-01"]),
        "App Received Date": pd.to_datetime(["2021-01-01", "2022-01-01", "2023-01-01"]),
        "App Complete Date": pd.to_datetime(["2021-03-01", "2022-03-01", "2023-03-01"]),
        "System Size DC": [100, 200, 300],
    })

    fig = application_time_bargraph(df)

    assert len(fig.data) == 2
    assert fig.data[0].name == "Rec-Comp"
    assert fig.data[1].name == "Comp-Appr"
    assert fig.layout.yaxis.title.text == "Application Time (Days)"


def test_electricity_rates_scatter_has_three_traces():
    df = pd.DataFrame({
        "Year": [2020, 2021, 2022],
        "US": [10.0, 11.0, 12.0],
        "CA": [15.0, 16.0, 17.0],
        "PGE": [20.0, 21.0, 22.0],
    })

    fig = electricity_rates_scatter(df)

    assert len(fig.data) == 3
    assert [t.name for t in fig.data] == ["US", "CA", "PGE"]
    assert fig.layout.yaxis.title.text == "Average Electricity Price (¢/kWh)"


def test_commercial_capacity_per_year_layout_size():
    df = _build_visualization_df()
    fig = commercial_capacity_per_year(df, layout_size=[800, 400])
    assert fig.layout.width == 800
    assert fig.layout.height == 400
    assert not fig.layout.autosize


def test_commercial_capacity_per_year_y_range():
    df = _build_visualization_df()
    fig = commercial_capacity_per_year(df, y_range=5000)
    assert fig.layout.yaxis.range[1] == 5000


def test_cost_shift_bargraph_structure():
    fig = cost_shift_bargraph()
    assert len(fig.data) == 2
    assert fig.data[0].x == ('PAO', 'CPUC', 'Borenstein', 'SolarWAVE', 'M.Cubed')
    assert fig.data[1].x == ('2024 Wildfire Spending', '2024 Net Profits', '2025 Net Profits')
    assert not fig.layout.showlegend


def test_cost_shift_bargraph_yaxis_range():
    fig = cost_shift_bargraph()
    assert fig.layout.yaxis.range[0] == -2
    assert fig.layout.yaxis.range[1] == 9


def _build_solar_graph_df():
    return pd.DataFrame({
        "NEM Tariff": ["1.0", "2.0", "NBT", "NBT"],
        "App Received Date": pd.to_datetime(
            ["2022-01-15", "2022-06-15", "2023-06-01", "2023-08-01"]
        ),
        "App Approved Date": pd.to_datetime(
            ["2022-02-01", "2022-07-01", "2023-07-01", "2023-09-01"]
        ),
        "System Size DC": [10.0, 20.0, 30.0, 40.0],
        "Customer Sector": ["Residential", "Residential", "Residential", "Residential"],
    })


def test_what_didnt_kill_rooftop_solar_graph_trace_names():
    df = _build_solar_graph_df()
    dates = [
        {"x0": "2021-06-01", "x1": "2022-12-01"},
        {"x0": "2023-04-15", "x1": "2024-06-01"},
    ]
    fig = what_didnt_kill_rooftop_solar_graph(df, dates, max_date="2024-01-01")
    trace_names = [t.name for t in fig.data]
    assert "NEM Applications" in trace_names
    assert "NBT Applications" in trace_names


def test_what_didnt_kill_rooftop_solar_graph_filters_non_residential():
    df = _build_solar_graph_df()
    df.loc[0, "Customer Sector"] = "Commercial"
    dates = [
        {"x0": "2021-06-01", "x1": "2022-12-01"},
        {"x0": "2023-04-15", "x1": "2024-06-01"},
    ]
    fig = what_didnt_kill_rooftop_solar_graph(df, dates, max_date="2024-01-01")
    nem_trace = next(t for t in fig.data if t.name == "NEM Applications")
    nem_total = sum(y for y in nem_trace.y if y is not None)
    assert nem_total == 20.0
