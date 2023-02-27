from datetime import datetime

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import streamlit as st

from allcause.data import age_recode_map, get_all_mortality_data
from allcause.excess_deaths import compute_excess_deaths


def get_excess_deaths_percentage_changes_for_all_age_ranges() -> pd.DataFrame:
    """Builds out the percentage changes in all cause deaths for all age ranges"""

    all_excess_deaths = pd.concat(
        [trend_map[sex][recode][1] for sex in sexes for recode in recodes]
    )
    age_range_deaths = (
        all_excess_deaths.groupby(["ager12", "sex"])[
            ["expected_deaths", "excess_deaths"]
        ]
        .sum()
        .reset_index()
    )

    age_range_deaths["% Excess Deaths"] = age_range_deaths.apply(
        lambda x: ((x.excess_deaths + x.expected_deaths) / x.expected_deaths - 1) * 100,
        axis=1,
    )

    age_range_deaths = age_range_deaths[age_range_deaths.ager12 < 12]

    age_range_deaths["ager12"] = age_range_deaths.ager12.apply(
        lambda x: age_recode_map[x]
    )

    return age_range_deaths.sort_values("% Excess Deaths", ascending=False)


sexes = ["M", "F"]
recodes = range(1, 13)

data = get_all_mortality_data()
data["yearmonth"] = data.apply(lambda x: datetime(x.year, x.monthdth, 1), axis=1)

trend_map = {
    sex: {recode: compute_excess_deaths(recode, sex, data) for recode in recodes}
    for sex in sexes
}


age_ranges = get_excess_deaths_percentage_changes_for_all_age_ranges()
