import pandas as pd

from data_visualization import commercial_capacity_per_year


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
    assert [annotation.text for annotation in fig.layout.annotations] == ["NBT", "AB 2143"]

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
