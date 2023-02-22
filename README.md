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

The files are cumbersome to download. This will take a while. You'll
be able to download most of them using the `get_all_mortality_data`
in the `allcause` package. The only exception is for the year 1969.
I hit some `utf-8` encoding errors when calling `pandas.read_csv`
on the link of the data but was able to circumvent them when I manually 
downloaded the data for this year. 

**Before running anything, you'll want to run the script `download_1969.py`**. 
This will download the 1969 data, munge it, and delete the downloaded
data. Or, you could do do it manually. This is just more convienent. 