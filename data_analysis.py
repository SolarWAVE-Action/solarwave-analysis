import argparse
import datetime
import glob
import numpy as np
import os
import pandas as pd
import warnings
from pandas.errors import PerformanceWarning

warnings.filterwarnings("ignore", category=PerformanceWarning)

"""
Analysis of energy data for SolarWAVE Action.

Author: Jenny Folkesson: jenny@solarwaveaction.org
"""


def read_dgstats_data(data_dir, archive_dir=None, date_min='2005-01-01'):
    """
    Read DGStats applications data files and combine them with DGStats archival
    files for analysis extending more than 5 years back in time.
    Data files for PG&E, SDG&E and SCE can be downloaded at:
    https://www.californiadgstats.ca.gov/downloads/

    :param str data_dir: Path to directory containing DGStats applications files
    :param str archive_dir: Path to directory containing DGStats archival files (separate)
    :param str date_min: Earliest date to keep in the data
    :return pd.DataFrame df: Dataframe containing all DGStats data (with to this
        analysis irrelevant columns removed)
    """
    # Find applications anr archive data based on the folder they're stored in
    file_names = glob.glob(os.path.join(data_dir, 'applications*5_year.csv'))
    archive_names = []
    if archive_dir is not None:
        archive_names = glob.glob(os.path.join(archive_dir, '*.csv'))
    # Read applications data
    dfs = []
    ious = []
    date_cutoff = datetime.datetime.today()
    for file_name in file_names:
        iou = file_name.split('_')[-3].upper()
        ious.append(iou)
        print("Reading file: ", file_name)
        df = pd.read_csv(file_name, low_memory=False)
        df['IOU'] = iou
        df['App Approved Date'] = pd.to_datetime(
            df['App Approved Date'], errors='coerce')
        date_temp = df['App Approved Date'].min()
        if date_temp < date_cutoff:
            date_cutoff = date_temp
        dfs.append(df)
    # Get the day before the earliest date to merge with archive
    date_cutoff = date_cutoff - datetime.timedelta(days=1)
    # Load archive data
    for iou in ious:
        # Look only for archives where IOU has an applications file
        file_match = [s for s in archive_names if iou in s]
        if len(file_match) == 1:
            print("Reading archive file: ", file_match[0])
            df = pd.read_csv(file_match[0], low_memory=False)
            df['IOU'] = iou
            df['App Approved Date'] = pd.to_datetime(
                df['App Approved Date'], errors='coerce')
            df = df[(df['App Approved Date'] >= date_min) &
                    (df['App Approved Date'] <= date_cutoff)]
            dfs.append(df)

    df_total = pd.concat(dfs, axis=0)
    # Only keep solar applications
    df_total = df_total[df_total['Technology Type'].str.contains('Photovoltaic')]
    df_total = df_total[df_total['System Size AC'] > 0]
    # According to the DGStats Download Interconnected Applications Data Set
    # Data Key, there should only be two main Application Status
    df_total = df_total[(df_total['Application Status'] == 'Interconnected') |
        (df_total['Application Status'] == 'Expansion-Solar, Storage') |
        (df_total['Application Status'] == 'Expansion-Solar,Storage') |
        (df_total['Application Status'] == 'Expansion-Solar PV, Storage') |
        (df_total['Application Status'] == 'APPROVED') |
        (df_total['Application Status'] == 'Expansion-Solar') |
        (df_total['Application Status'] == 'Exp-Solar, Storage') |
        (df_total['Application Status'] == 'Commercial')]
    # Convert all dates to datetime objects
    df_total['App Received Date'] = pd.to_datetime(
        df_total['App Received Date'], errors='coerce')
    df_total['App Complete Date'] = pd.to_datetime(
        df_total['App Complete Date'], errors='coerce')
    df_total['App Approved Date'] = pd.to_datetime(
        df_total['App Approved Date'], errors='coerce')
    # Remove irrelevant columns
    cols = ['IOU'] + [c for c in df_total.columns if c != 'IOU']
    df_total = df_total[cols].iloc[:, :47]
    df_total = df_total.drop(
        columns=['System Output Monitoring Provider',
                 'System Output Reports To Vendor?',
                 'System Output Monitoring',
                 'Pace Financier', 'Service Zip',
                 'CSLB Number', 'Matched CSI Application Number',
                 'Electric Vehicle', 'Electric Vehicle Count',
                 'Itc Cost Basis', 'Third Party Owned Type',
                 'Installer Zip', 'Installer State',
                 'Installer City', 'Installer Phone',
                 'Preceding Id', 'Superceding Id', 'Application Id'])
    return df_total


def compile_electricity_rates(data_dir, eia_csv=None, cpuc_csv=None):
    """
    Combine US and CA rates from EIA with PG&E data from CPUC and inflation data
    from FRED.
    EIA data can be downloaded from: https://www.eia.gov/electricity/data/browser/
    CPUC historic electric cost data can be downloaded from Ecxel download here:
    https://www.cpuc.ca.gov/industries-and-topics/electrical-energy/electric-costs/historical-electric-cost-data
    I saved only the first sheet from that file into a csv and read that.

    :param str data_dir: csv files containing the downloaded tables
    :param str eia_csv: File name of EIA average retail electricity data
    :param str cpuc_csv: File name of CPUC bundled system average rates
    :return pd.DataFrame df: Inflation adjusted bundled average rates
    """
    # Fall back on the names I saved the files as if not specified
    if eia_csv is None:
        eia_csv = 'EIA-Average_retail_price_of_electricity_us_ca.csv'
    if cpuc_csv is None:
        cpuc_csv = 'CPUC-Bundled System Average Rate.csv'

    file_name = os.path.join(data_dir, eia_csv)
    df_eia = pd.read_csv(file_name, skiprows=4)
    df_eia = df_eia.drop(columns=['units', 'source key'])
    df_eia = df_eia.set_index('description')
    df_eia = df_eia.T
    df_eia = df_eia[['United States : all sectors', 'California : all sectors']]
    df_eia['Year'] = pd.to_numeric(df_eia.index, downcast='integer', errors='coerce')

    file_name = os.path.join(data_dir, cpuc_csv)
    df_pge = pd.read_csv(file_name, skiprows=2)
    df_pge = df_pge.loc[0:2, :]
    df_pge = df_pge.drop(columns=['Unnamed: 0', 'Unnamed: 21'])
    df_pge = df_pge.set_index('Utility')
    df_pge = df_pge.T
    df_pge['Year'] = pd.to_numeric(df_pge.index, downcast='integer', errors='coerce')

    # Join dataframes
    df = pd.merge(df_eia, df_pge, on='Year', how='left')

    # Adjust for inflation using FRED CPI
    df_cpi = pd.read_csv(os.path.join(data_dir, 'CPIAUCNS.csv'))
    df_cpi['observation_date'] = pd.to_datetime(df_cpi['observation_date'], format='%Y-%m-%d')
    df_cpi['Year'] = df_cpi['observation_date'].dt.year
    # Join dataframes
    df = pd.merge(df, df_cpi, on='Year')

    df.rename(columns={'United States : all sectors': 'US',
                       'California : all sectors': 'CA',
                       'PG&E ': 'PGE'},
              inplace=True)
    df['US'] = pd.to_numeric(df['US'], downcast='float', errors='coerce')
    df['CA'] = pd.to_numeric(df['CA'], downcast='float', errors='coerce')
    df['US'] = df['US'].div(df['CPIAUCNS']) * df.iloc[-1]['CPIAUCNS']
    df['CA'] = df['CA'].div(df['CPIAUCNS']) * df.iloc[-1]['CPIAUCNS']
    df['PGE'] = df['PGE'].div(df['CPIAUCNS']) * df.iloc[-1]['CPIAUCNS']
    return df


def cost_forecast(nbr_years, production, price, price_increase, degradation):
    """
    Simple estimator of cost and savings forecast for a solar system.
    Electicity prices are assumed to increase with a fixed percentage each year,
    and production is assumed to decrease with a fixed percentage each year.

    :param int nbr_years: Number of years system is used (e.g. 25)
    :param float production: Estimated production of system in the first year
    :param float price: First year electricity price per kWh
    :param float price_increase: Estimated annual electricity price increase in percent
    :param float degradation: Estimated annual system degradation in percent
    :return pd.DataFrame df: Datafram with production, rate, annual savings, and
        cumulative savings for the years [1:nbr_years]
    """
    df = pd.DataFrame(index=np.arange(1, nbr_years + 1),
                      columns=["Production (kWh)", "Rate ($/kWh)", "Annual Savings ($)", "Cumulative Savings ($)"])
    df.loc[1, :] = [production, price, production * price, production * price]

    for i in range(1, len(df)):
        today = df.index[i]
        last_year = df.index[i - 1]
        df.loc[today, "Production (kWh)"] = df.loc[last_year, "Production (kWh)"] * (1 - degradation / 100)
        df.loc[today, "Rate ($/kWh)"] = df.loc[last_year, "Rate ($/kWh)"] * (1 + price_increase / 100)
        df.loc[today, "Annual Savings ($)"] = df.loc[today, "Production (kWh)"] * df.loc[today, "Rate ($/kWh)"]
        df.loc[today, "Cumulative Savings ($)"] = df.loc[last_year, "Cumulative Savings ($)"] + df.loc[today, "Annual Savings ($)"]

    df['Production (kWh)'] = df['Production (kWh)'].apply(lambda x: f'{int(round(x, 0)):,}')
    df['Rate ($/kWh)'] = df['Rate ($/kWh)'].apply(lambda x: round(x, 2))
    df['Annual Savings ($)'] = df['Annual Savings ($)'].apply(lambda x: int(round(x, 0)))
    df['Cumulative Savings ($)'] = df['Cumulative Savings ($)'].apply(lambda x: f'{int(round(x, 0)):,}')

    return df






