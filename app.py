from datetime import datetime
from typing import List

import pandas as pd
import plotly.express as px
import streamlit as st

from allcause.data import age_recode_map, get_all_mortality_data
from allcause.excess_deaths import compute_excess_deaths


def get_excess_deaths_percentage_changes_for_all_age_ranges(
    columns_agg: List[str] = ["ager12", "sex"]
) -> pd.DataFrame:
    """Builds out the percentage changes in all cause deaths for all age ranges"""

    all_excess_deaths = pd.concat(
        [trend_map[sex][recode][1] for sex in sexes for recode in recodes]
    )
    age_range_deaths = (
        all_excess_deaths.groupby(columns_agg)[["expected_deaths", "excess_deaths"]]
        .sum()
        .reset_index()
    )

    age_range_deaths["% Excess Deaths Increase"] = age_range_deaths.apply(
        lambda x: ((x.excess_deaths + x.expected_deaths) / x.expected_deaths - 1) * 100,
        axis=1,
    )

    age_range_deaths = age_range_deaths[age_range_deaths.ager12 < 12]

    age_range_deaths["ager12"] = age_range_deaths.ager12.apply(
        lambda x: age_recode_map[x]
    )

    age_range_deaths = age_range_deaths.sort_values(
        "% Excess Deaths Increase", ascending=False
    )

    age_range_deaths["Sex"] = age_range_deaths.sex.apply(
        lambda x: "Males" if x == "M" else "Females"
    )
    age_range_deaths["Demographic"] = age_range_deaths.apply(
        lambda x: f"{x.Sex} age {x.ager12}", axis=1
    )

    return age_range_deaths


@st.cache_data
def build_trend_map(recodes, sexes):

    return {
        sex: {recode: compute_excess_deaths(recode, sex, data) for recode in recodes}
        for sex in sexes
    }


sex_map = {"Male": "M", "Female": "F"}


sexes = ["M", "F"]
recodes = list(range(2, 12))

inverse_recodes = {v: k for k, v in age_recode_map.items()}
recode_name_list = [age_recode_map[x] for x in recodes]

data = get_all_mortality_data()
data["yearmonth"] = data.apply(lambda x: datetime(x.year, x.monthdth, 1), axis=1)

trend_map = build_trend_map(recodes, sexes)


age_ranges = get_excess_deaths_percentage_changes_for_all_age_ranges()
age_range_time = get_excess_deaths_percentage_changes_for_all_age_ranges(
    ["yearmonth", "ager12", "sex"]
)

st.write(
    """
    # 2021 - 2022 All Cause Mortality Trends
    
    Expected all cause deaths follow a predictable pattern on a year by year basis - this 
    application uses data from 2020-2019 to estimate the expected deaths in 2020 and 2021. All
    data comes from [the NBER](https://www.nber.org/research/data/mortality-data-vital-statistics-nchs-multiple-cause-death-data).
      
    Do the excess death patterns fit a respiratory virus, or is there something else at play? 
    
    ## Demographic Percentage Trends
    The following charts compare percentage changes in excess deaths across demographics
    """
)

sexes_percent = st.multiselect("Select sexes to display", ["Male", "Female"], ["Male"])

sexes_percent = [sex_map[x] for x in sexes_percent]

ages_percent = st.multiselect(
    "Select ages to display",
    recode_name_list,
    ["25-34 years", "35-44 years", "75-84 years"],
)


age_range_plt = age_ranges[
    age_ranges.sex.isin(sexes_percent) & age_ranges.ager12.isin(ages_percent)
]
fig = px.bar(
    age_range_plt,
    y="Demographic",
    x="% Excess Deaths Increase",
    orientation="h",
    title="% Changes in Excess Deaths 2020-2021 from 2020-2019 Trends",
)

st.plotly_chart(fig, caption="Embiggen the chart to see all demographics")

age_range_time = age_range_time.rename({"yearmonth": "Month"}, axis=1).sort_values(
    ["Demographic", "Month"]
)
monthly_fig = px.line(
    age_range_time[
        age_range_time.sex.isin(sexes_percent)
        & age_range_time.ager12.isin(ages_percent)
    ],
    x="Month",
    y="% Excess Deaths Increase",
    color="Demographic",
    title="Monthly % Changes in Excess Deaths 2020-2021 from 2020-2019 Trends",
)

st.plotly_chart(monthly_fig)


st.write(
    """
## Isolated Trends
This section of the app displays trends for individual demographic groups
"""
)

sex = st.selectbox("Select a Sex to View In Depth Charts", ["Male", "Female"])

sex_coded = sex_map[sex]

recode = st.selectbox("Select an Age Range to View In Depth Charts", recode_name_list)

recode_coded = inverse_recodes[recode]

excess_fig = trend_map[sex_coded][recode_coded][0]
all_cause_trend_fig = trend_map[sex_coded][recode_coded][2]
st.pyplot(excess_fig)
st.pyplot(all_cause_trend_fig)
