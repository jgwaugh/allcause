import os
from datetime import datetime
from pathlib import Path

import httplib2
import joblib
import pandas as pd
from bs4 import BeautifulSoup, SoupStrainer

DATALINK = "https://www.nber.org/research/data/mortality-data-vital-statistics-nchs-multiple-cause-death-data"

age_recode_map = {
    1: "<1 year",
    2: "1-4 years",
    3: "5-14 years",
    4: "15-24 years",
    5: "25-34 years",
    6: "35-44 years",
    7: "45-54 years",
    8: "55-64 years",
    9: "65-74 years",
    10: "75-84 years",
    11: "85+ years",
    12: "Age not stated",
}


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
                if year == 1969:
                    pd.read_csv(link["href"], encoding_errors="ignore")
                else:
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
    path = Path(__file__).parents[0].joinpath("cache")
    if not os.path.exists(path):
        os.makedirs(path)
    return path


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


def get_all_mortality_data(
    year_start: int = 2000, year_end: int = 2022
) -> pd.DataFrame:
    """Loads all mortality data"""

    years = [get_yearly_mortality_data(year) for year in range(year_start, min(year_end, 2022))]

    if year_end == 2023:
        years += [get_nber_2022_all_cause_approximation()]
    return pd.concat(years)

def get_vaccination_data() -> pd.DataFrame:
    """Gets the vaccination data
    Data comes from here: https://data.cdc.gov/Vaccinations/Archive-COVID-19-Vaccination-and-Case-Trends-by-Ag/gxj9-t96f
    """
    data = pd.read_csv(path_to_cache().joinpath("vaccination_data.csv"))
    data["date"] = data["Date Administered"].map(pd.to_datetime)
    data["day"] = data.date.map(lambda x: x.day)
    return data


def get_covid_data() -> pd.DataFrame:
    """Gets the COVID data, which also has some all cause data
    Data comes from here: https://data.cdc.gov/NCHS/Provisional-COVID-19-Deaths-by-Week-Sex-and-Age/vsak-wrfu
    """
    return pd.read_csv(path_to_cache().joinpath("covid_deaths.csv"))


def get_cdc_all_cause() -> pd.DataFrame:
    """Loads the cdc all covid data and uses it to compute all cause data (no all cause yet for 2022)"""
    cdc_all_cause = get_covid_data()
    cdc_all_cause["End Week"] = cdc_all_cause["End Week"].map(pd.to_datetime)
    cdc_all_cause["yearmonth"] = cdc_all_cause["End Week"].map(
        lambda x: datetime(x.year, x.month, 1)
    )
    cdc_all_cause = cdc_all_cause[
        cdc_all_cause.Sex.isin(["Male", "Female"])
        & (cdc_all_cause.State == "United States")
    ]
    cdc_all_cause = cdc_all_cause.rename(
        {
            "Total Deaths": "death_count",
            "COVID-19 Deaths": "covid_deaths",
            "Sex": "sex",
        },
        axis=1,
    )

    cdc_all_cause = (
        cdc_all_cause.groupby(["sex", "Age Group", "yearmonth"])[
            ["death_count", "covid_deaths"]
        ]
        .sum()
        .reset_index()
    )

    cdc_all_cause["Age Group"] = cdc_all_cause["Age Group"].map(
        lambda x: x.lower().replace("under ", "<").replace(" years and over", "+ years")
    )
    inverse_recode_map = {v: k for k, v in age_recode_map.items()}
    cdc_all_cause = cdc_all_cause.rename({"Age Group": "ager12"}, axis=1)
    cdc_all_cause = cdc_all_cause[cdc_all_cause.ager12 != "all ages"]
    cdc_all_cause["ager12"] = cdc_all_cause["ager12"].map(
        lambda x: inverse_recode_map[x]
    )
    cdc_all_cause["sex"] = cdc_all_cause["sex"].map(lambda x: x[0])
    cdc_all_cause = cdc_all_cause.drop("covid_deaths", axis=1)
    cdc_all_cause["monthdth"] = cdc_all_cause.yearmonth.apply(lambda x: x.month)
    cdc_all_cause["year"] = cdc_all_cause.yearmonth.apply(lambda x: x.year)
    return cdc_all_cause


def get_nber_2022_all_cause_approximation() -> pd.DataFrame:
    """
    Uses a random forest regressor to predict the 2022 NBER
    all cause mortality estimates based on the CDC data. For
    more information, see the `modeling` folder in the main project.

    Returns
    -------
    pandas Dataframe
        Dataframe with CDC death counts transformed to NBER sizes

    """
    cdc_data = get_cdc_all_cause()
    model = joblib.load(path_to_cache().joinpath("nber_data_approximator"))
    cdc_data = cdc_data[cdc_data.year == 2022]
    cdc_data = cdc_data.rename({"death_count": "cdc_death_count"}, axis=1)

    cdc_data["death_count"] = model.predict(cdc_data)
    return cdc_data.drop("cdc_death_count", axis=1)
