from datetime import datetime

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import streamlit as st

import plotly.express as px


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

    age_range_deaths["% Excess Deaths Increase"] = age_range_deaths.apply(
        lambda x: ((x.excess_deaths + x.expected_deaths) / x.expected_deaths - 1) * 100,
        axis=1,
    )

    age_range_deaths = age_range_deaths[age_range_deaths.ager12 < 12]

    age_range_deaths["ager12"] = age_range_deaths.ager12.apply(
        lambda x: age_recode_map[x]
    )

    age_range_deaths = age_range_deaths.sort_values("% Excess Deaths Increase", ascending=False)

    age_range_deaths = age_range_deaths.rename({'ager12': 'Demographic', }, axis=1)
    age_range_deaths['Sex'] = age_range_deaths.sex.apply(lambda x: 'Males' if x == 'M' else 'Females')
    age_range_deaths['Demographic'] = age_range_deaths.apply(lambda x: f'{x.Sex} age {x.Demographic}', axis=1)

    return age_range_deaths

@st.cache_data
def build_trend_map(recodes, sexes):

    return {
    sex: {recode: compute_excess_deaths(recode, sex, data) for recode in recodes}
    for sex in sexes
}


sns.set()

sexes = ["M", "F"]
recodes = list(range(2, 6))

inverse_recodes = {v : k for k, v in age_recode_map.items()}
recode_name_list = [age_recode_map[x] for x in recodes]

data = get_all_mortality_data()
data["yearmonth"] = data.apply(lambda x: datetime(x.year, x.monthdth, 1), axis=1)

trend_map = build_trend_map(recodes, sexes)


age_ranges = get_excess_deaths_percentage_changes_for_all_age_ranges()


st.write(
    """
    # 2021 - 2022 All Cause Mortality Trends
    
    Expected all cause deaths follow a predictable pattern on a year by year basis - this 
    application uses data from 2020-2019 to estimate the expected deaths in 2020 and 2021. 
    
    Do the excess death patterns fit a respiratory virus, or is there something else at play? 
    """
)


fig = px.bar(age_ranges, y="Demographic", x="% Excess Deaths Increase", orientation='h',
             title='% Changes in Excess Deaths 2020-2021 from 2020-2019 Trends')

st.plotly_chart(fig)

sex = st.selectbox(
    'Select a Sex to View In Depth Charts',
    ['Male', 'Female'])

if sex == 'Male':
    sex_coded = 'M'
else:
    sex_coded = 'F'

recode = st.selectbox(
    'Select an Age Range to View In Depth Charts',
    recode_name_list
)

recode_coded = inverse_recodes[recode]

excess_fig = trend_map[sex_coded][recode_coded][0]
all_cause_trend_fig = trend_map[sex_coded][recode_coded][2]
st.pyplot(excess_fig)
st.pyplot(all_cause_trend_fig)