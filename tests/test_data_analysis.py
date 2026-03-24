import pandas as pd
import pytest

from data_analysis import cost_forecast, read_dgstats_data


DROP_COLS = [
    "System Output Monitoring Provider",
    "System Output Reports To Vendor?",
    "System Output Monitoring",
    "Pace Financier",
    "Service Zip",
    "CSLB Number",
    "Matched CSI Application Number",
    'Electric Vehicle',
    'Electric Vehicle Count',
    'Itc Cost Basis',
    'Third Party Owned Type',
    "Installer Zip",
    "Installer State",
    "Installer City",
    "Installer Phone",
    "Preceding Id",
    "Superceding Id",
    "Application Id",
]

REQUIRED_COLS = [
    "App Approved Date",
    "Technology Type",
    "System Size AC",
    "App Received Date",
    "App Complete Date",
    "Application Status",
    "Decommissioned Date",
    "Tilt",
    "Azimuth",
    "NEM Tariff",
]


def _build_df(rows):
    columns = REQUIRED_COLS + DROP_COLS
    # Ensure at least 46 columns total so slicing does not drop required columns.
    needed_dummy = 46 - len(columns)
    dummy_cols = [f"Dummy {i}" for i in range(needed_dummy)]
    columns = columns + dummy_cols

    df = pd.DataFrame(rows)
    for col in columns:
        if col not in df.columns:
            df[col] = ""
    return df[columns]


def _write_csv(df, path):
    df.to_csv(path, index=False)


def test_read_dgstats_data_filters_and_merges_archives(tmp_path):
    data_dir = tmp_path / "data"
    archive_dir = tmp_path / "archive"
    data_dir.mkdir()
    archive_dir.mkdir()

    app_rows = [
        {
            "App Approved Date": "2020-01-10",
            "Technology Type": "Photovoltaic",
            "System Size AC": 5,
            "App Received Date": "2020-01-01",
            "App Complete Date": "2020-01-05",
            "Application Status": "Interconnected",
        },
        {
            "App Approved Date": "2020-02-01",
            "Technology Type": "Wind",
            "System Size AC": 5,
            "App Received Date": "2020-01-15",
            "App Complete Date": "2020-01-20",
            "Application Status": "Interconnected",
        },
        {
            "App Approved Date": "2020-03-01",
            "Technology Type": "Photovoltaic",
            "System Size AC": 0,
            "App Received Date": "2020-02-01",
            "App Complete Date": "2020-02-10",
            "Application Status": "DECOMMISSIONED-DESTROYED",
        },
    ]

    archive_rows = [
        {
            "App Approved Date": "2019-12-15",
            "Technology Type": "Photovoltaic",
            "System Size AC": 3,
            "App Received Date": "2019-12-01",
            "App Complete Date": "2019-12-05",
            "Application Status": "Interconnected",
        },
        {
            "App Approved Date": "2020-01-10",
            "Technology Type": "Photovoltaic",
            "System Size AC": 4,
            "App Received Date": "2020-01-01",
            "App Complete Date": "2020-01-02",
            "Application Status": "Interconnected",
        },
    ]

    app_df = _build_df(app_rows)
    archive_df = _build_df(archive_rows)

    _write_csv(app_df, data_dir / "applications_pge_5_year.csv")
    _write_csv(archive_df, archive_dir / "archive_PGE.csv")

    result = read_dgstats_data(
        data_dir=str(data_dir),
        archive_dir=str(archive_dir),
        date_min="2019-01-01",
    )
    # Only two rows should remain: one from applications + one from archive
    assert len(result) == 2
    assert set(result["IOU"].unique()) == {"PGE"}

    # Filtered to solar + positive size
    assert all(result["Technology Type"].str.contains("Photovoltaic"))
    assert (result["System Size AC"] > 0).all()

    # Dates parsed
    assert pd.api.types.is_datetime64_any_dtype(result["App Approved Date"])
    assert pd.api.types.is_datetime64_any_dtype(result["App Received Date"])
    assert pd.api.types.is_datetime64_any_dtype(result["App Complete Date"])

    # Dropped columns are removed
    for col in DROP_COLS:
        assert col not in result.columns


def test_read_dgstats_data_without_archive_dir(tmp_path):
    data_dir = tmp_path / "data"
    data_dir.mkdir()

    app_rows = [
        {
            "App Approved Date": "2021-05-10",
            "Technology Type": "Photovoltaic",
            "System Size AC": 2,
            "App Received Date": "2021-05-01",
            "App Complete Date": "2021-05-05",
            "Application Status": "Interconnected",
        }
    ]

    app_df = _build_df(app_rows)
    _write_csv(app_df, data_dir / "applications_sce_5_year.csv")

    result = read_dgstats_data(data_dir=str(data_dir), archive_dir=None)
    assert len(result) == 1
    assert set(result["IOU"].unique()) == {"SCE"}


def test_cost_forecast_shape():
    df = cost_forecast(nbr_years=5, production=1000, price=0.20, price_increase=3, degradation=0.5)
    assert len(df) == 5
    assert list(df.columns) == ["Production (kWh)", "Rate ($/kWh)", "Annual Savings ($)", "Cumulative Savings ($)"]


def test_cost_forecast_first_year_values():
    df = cost_forecast(nbr_years=3, production=1000, price=0.20, price_increase=0, degradation=0)
    assert df.loc[1, "Annual Savings ($)"] == 200
    assert df.loc[1, "Production (kWh)"] == "1,000"


def test_cost_forecast_degradation_reduces_production():
    df = cost_forecast(nbr_years=3, production=1000, price=0.20, price_increase=0, degradation=10)
    prod_1 = int(df.loc[1, "Production (kWh)"].replace(",", ""))
    prod_2 = int(df.loc[2, "Production (kWh)"].replace(",", ""))
    assert prod_2 < prod_1


def test_cost_forecast_price_increase_raises_rate():
    df = cost_forecast(nbr_years=3, production=1000, price=0.20, price_increase=10, degradation=0)
    rate_1 = float(df.loc[1, "Rate ($/kWh)"])
    rate_2 = float(df.loc[2, "Rate ($/kWh)"])
    assert rate_2 > rate_1
