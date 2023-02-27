from datetime import datetime
from typing import List, Tuple

import matplotlib.pyplot as plt
import pandas as pd
from prophet import Prophet

from allcause.data import age_recode_map

sex_map = {"M": "Males", "F": "Females"}

image = plt.figure


def compute_excess_deaths(
    agerecode: int,
    sex: str,
    data: pd.DataFrame,
    years_train: List[int] = list(range(2000, 2020)),
    years_test: List[int] = [2020, 2021],
) -> Tuple[image, pd.DataFrame, image]:
    """

     Uses timeseries modeling to computed excess deaths for all cause mortality, with
     nonlinear trends and seasonality.

    Parameters
    ----------
    agerecode : int
         The 12 bracket age recode to filter the data to
    sex : str
         The sex (Male or Female) to filter the data to
    data : pandas dataframe
         Data containing all cause counts over time
    years_train : List[int]
         The years to use in computing all cause mortality trends. Defaults to 2000 to 2019.
    years_test : List[int]
         The years to use in computing excess deaths. Defaults to 2020 and 2021.

    Returns
    -------
    tuple
         image of excess death trends, raw excess death data, and image of all cause trends

    """

    train_cols = ["yearmonth", "death_count"]
    rename_map = {"yearmonth": "ds", "death_count": "y"}

    data_use = data[(data.sex == sex) & (data.ager12 == agerecode)]

    train = data_use[data_use.year.isin(years_train)][train_cols].rename(
        rename_map, axis=1
    )
    test = data_use[data_use.year.isin(years_test)][train_cols].rename(
        rename_map, axis=1
    )

    m = Prophet(weekly_seasonality=False, daily_seasonality=False)

    m.fit(train)

    future = m.make_future_dataframe(periods=25, freq="M")
    future["ds"] = future.ds.apply(lambda x: datetime(x.year, x.month, 1))
    forecast = m.predict(future)

    all_cause_trend_fig = m.plot(forecast)
    plt.plot(test["ds"], test["y"], color="red")
    plt.xlabel("Year")
    plt.ylabel("All Cause Deaths")
    plt.title(f"All Cause Death Trends for {sex_map[sex]} aged {age_recode_map[agerecode]}")

    future_forecast = forecast[forecast.ds >= datetime(2020, 1, 1)]
    excess_deaths = test["y"].values - future_forecast["yhat"].values

    excess_fig = plt.figure()
    plt.plot(test.ds, excess_deaths)
    plt.xticks(rotation=30)
    plt.ylabel("Excess Deaths")
    plt.title(f"Excess Deaths for {sex_map[sex]} aged {age_recode_map[agerecode]}")

    excess_trend_df = pd.DataFrame(
        {
            "yearmonth": test.ds.values,
            "excess_deaths": excess_deaths,
            "expected_deaths": future_forecast["yhat"].values,
        }
    )

    excess_trend_df["sex"] = sex
    excess_trend_df["ager12"] = agerecode

    return excess_fig, excess_trend_df, all_cause_trend_fig
