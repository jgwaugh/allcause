from pathlib import Path

import httplib2
import pandas as pd
from bs4 import BeautifulSoup, SoupStrainer

DATALINK = "https://www.nber.org/research/data/mortality-data-vital-statistics-nchs-multiple-cause-death-data"


def download_year_mortality_data(year: int) -> pd.DataFrame:
    """
    Downloads a year's worth of data from the internet

    Parameters
    ----------
    year : int
        The year to scrape

    Returns
    -------
    pandas dataframe
        Year's worth of mortality data

    """

    if year == 2021:
        id_string = "mort2021us.csv"
    elif year >= 2018:
        id_string = f"Mort{year}US.PubUse.csv"
    else:
        id_string = f"mort{year}.csv.zip"

    http = httplib2.Http()
    status, response = http.request(DATALINK)

    for link in BeautifulSoup(response, parse_only=SoupStrainer("a")):
        if link.has_attr("href"):
            if id_string in link["href"]:
                return pd.read_csv(link["href"])


def munge_data(df: pd.DataFrame, year: int) -> pd.DataFrame:
    """
    Aggregates all cause mortality data to the level of interest
    for the analysis.

    Parameters
    ----------
    df : pandas dataframe
       Data at the person level
    year : int
        The year of the mortality data

    Returns
    -------
    pandas dataframe
        Data at the month/ sex / age range level

    """

    group_cols = ["ager12", "monthdth", "sex"]
    df_grouped = (
        df.groupby(group_cols).size().reset_index().rename({0: "death_count"}, axis=1)
    )
    df_grouped["year"] = year

    # transform the integer death codes
    if df_grouped.dtypes["sex"] != "O":
        df_grouped["sex"] = df_grouped["sex"].map(lambda x: "M" if x == 1 else "F")

    return df_grouped


def path_to_cache() -> Path:
    """Path to the data cache"""
    return Path(__file__).parents[0].joinpath("cache")


def get_yearly_mortality_data(year: int) -> pd.DataFrame:
    """
    Gets the yearly mortality data for a given year.
    If not saved locally, downloads it

    Parameters
    ----------
    year: int
        Year of data to retrieve

    Returns
    -------
    pandas dataframe
        Aggregated all cause mortality data for that year
    """
    file_path = path_to_cache().joinpath(f"{year}.pkl")
    try:
        return pd.read_pickle(file_path)
    except FileNotFoundError:
        data = download_year_mortality_data(year)
        data_munged = munge_data(data, year)
        del data  # deletes this from memory to avoid overflow issues
        data_munged.to_pickle(file_path)
        return data_munged


def get_all_mortality_data() -> pd.DataFrame:
    """Loads all mortality data"""
    return pd.concat([get_yearly_mortality_data(year) for year in range(1959, 2022)])
