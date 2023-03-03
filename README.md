# All Cause Mortality Modeling

This repo contains all cause mortality data analysis.


## Setup

Modeling was done in `python 3.9.16`. Virtual environments
were managed with `conda`. 

To get started, run 

```
conda create allcause python=3.9.16 && conda activate allcause
```

To install requirements, run `pip install -r requirements.txt`

## Data 

### Downloading 2022 Data

To download the CDC data for 2022, run the following `source download_cdc.py`.
This should be fairly quick. 

### NBER Programatic Download

NBER data takes a while to download. To get everything, run
 
```
source get_data.sh
```

in the command line. 
**If you don't need data from 1969, you can skip this step. Just expect
long wait times in the app as you will be downloading data when you first 
run it.**

#### Explanation
Most files can be download using the `get_all_mortality_data`
in the `allcause` package. The only exception is for the year 1969.
I hit some `utf-8` encoding errors when calling `pandas.read_csv`
on the link of the data but was able to circumvent them when I manually 
downloaded the data for this year. 

**Before running anything, you'll want to run the script `download_1969.py`**. 
This will download the 1969 data, munge it, and delete the downloaded
data. Or, you could do it manually. This is just more convenient. You will 
need to [install Google Chrome](https://www.google.com/chrome/dr/download/?brand=SLLM&geo=US&gclid=CjwKCAiAxvGfBhB-EiwAMPakqqmyw6YWuXBhWu9TCAEIlccn-nrh3fC6w6p1mlhsbEovVZlgVwhG9RoCzNwQAvD_BwE&gclsrc=aw.ds)
to run this script. 

If this is taking a long time, adjust the `SECONDS_SLEEP` parameter in
`download_1969.py` - the program sleeps while the file downloads. I could
probably do this with a promise, but I've got better things to do. 

## Running

To view excess death data, run `streamlit run app.py` in a terminal shell. 