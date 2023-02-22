import time
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

import pandas as pd

from allcause.data import munge_data, DATALINK

import os
import zipfile

SECONDS_SLEEP = 60 * 10


##################################################
#
# Find paths where data will be downloaded to
#
##################################################

path_to_cache = Path(__file__).parents[0].joinpath("allcause").joinpath("cache")
path_to_download = '~/Downloads/mort1969.csv.zip'
abs_path_to_download = os.popen(f'ls {path_to_download}').read().replace('\n', '')


##################################################
#
# Download the data with Selenium
#
##################################################

driver = webdriver.Chrome(ChromeDriverManager().install())
driver.get(DATALINK)

lnks = driver.find_elements(By.TAG_NAME, "a")
# traverse list
for lnk in lnks:
    link_string = lnk.get_attribute("href")
    if type(link_string) != type(None):
        if "mort1969.csv" in link_string:
            lnk.click()
            break

time.sleep(SECONDS_SLEEP) # wait for download


##################################################
#
# Munge the downloaded data
#
##################################################

# unzip data
with zipfile.ZipFile(abs_path_to_download, 'r') as zip_ref:
    parent_path = Path(abs_path_to_download).parents[0]
    zip_ref.extractall(parent_path)


data = pd.read_csv(path_to_download, encoding_errors='ignore')

data = munge_data(data, 1969)

data.to_pickle(path_to_cache.joinpath('1969.pkl'))
os.remove(abs_path_to_download) # remove zip file
os.remove(abs_path_to_download[:-4]) # remove unzipped data

driver.quit()


