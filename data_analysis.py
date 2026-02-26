import argparse
import datetime
import glob
import numpy as np
import os
import pandas as pd

"""
Analysis of energy data for SolarWAVE Action.

Author: Jenny Folkesson, PhD. jenny@solarwaveaction.org
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

        df = pd.read_csv(file_name, low_memory=False)
        df.insert(1, 'IOU', iou)
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
            df = pd.read_csv(file_match[0], low_memory=False)
            # df['IOU'] = iou
            df.insert(1, 'IOU', iou)
            df['App Approved Date'] = pd.to_datetime(
                df['App Approved Date'], errors='coerce')
            df = df[(df['App Approved Date'] >= date_min) &
                    (df['App Approved Date'] <= date_cutoff)]
            dfs.append(df)

    df_total = pd.concat(dfs, axis=0)
    # Only use solar applications
    df_total = df_total[df_total['Technology Type'].str.contains('Photovoltaic')]
    df_total = df_total[df_total['System Size AC'] > 0]
    # Convert all dates to datetime objects
    df_total['App Received Date'] = pd.to_datetime(
        df_total['App Received Date'], errors='coerce')
    df_total['App Complete Date'] = pd.to_datetime(
        df_total['App Complete Date'], errors='coerce')
    df_total['App Approved Date'] = pd.to_datetime(
        df_total['App Approved Date'], errors='coerce')
    # Remove irrelevant columns
    df_total = df_total.iloc[:, :47]
    df_total = df_total.drop(
        columns=['System Output Monitoring Provider',
                 'System Output Reports To Vendor?',
                 'System Output Monitoring',
                 'Pace Financier', 'Service Zip',
                 'CSLB Number', 'Matched CSI Application Number',
                 'Installer Zip', 'Installer State',
                 'Installer City', 'Installer Phone',
                 'Preceding Id', 'Superceding Id', 'Application Id'])
    return df_total







