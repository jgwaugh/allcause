import os
import time

import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

from allcause.data import path_to_cache

SECONDS_SLEEP = 15
cdc_link = "https://data.cdc.gov/NCHS/Provisional-COVID-19-Deaths-by-Week-Sex-and-Age/vsak-wrfu"

##################################################
#
# Find paths where data will be downloaded to
#
##################################################

path_to_cache = path_to_cache()


##################################################
#
# Download the data with Selenium
#
##################################################

driver = webdriver.Chrome(ChromeDriverManager().install())
driver.get(cdc_link)

button = driver.find_elements(By.CSS_SELECTOR, ".btn.btn-simple.btn-sm.download")
button[0].click()

lnks = driver.find_elements(By.TAG_NAME, "a")
# traverse list
for lnk in lnks:
    link_string = lnk.get_attribute("href")
    if type(link_string) != type(None):
        if "rows.csv?accessType=DOWNLOAD" in link_string:
            lnk.click()
            break

time.sleep(SECONDS_SLEEP)  # wait for download


##################################################
#
# Munge the downloaded data
#
##################################################

path_to_download = "~/Downloads/Provisional_COVID-19_Deaths_by_Week__Sex__and_Age.csv"
abs_path_to_download = os.popen(f"ls {path_to_download}").read().replace("\n", "")

data = pd.read_csv(path_to_download, encoding_errors="ignore")

data.to_csv(path_to_cache.joinpath("covid_deaths.csv"))
os.remove(abs_path_to_download)  # remove downloaded data

driver.quit()
