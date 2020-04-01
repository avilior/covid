#!/usr/bin/env python

# source https://github.com/CSSEGISandData/COVID-19/tree/master/csse_covid_19_data/csse_covid_19_time_series

import wget
import shutil
from pathlib import Path
import logging


from config import INDATADIR, LOCAL_CONFIRMED, LOCAL_DEATHS

LOG = logging.getLogger(__name__)

INDATADIR = INDATADIR.resolve()


# deprecated
#URL_CONFIRMED = "https://github.com/CSSEGISandData/COVID-19/raw/master/csse_covid_19_data/csse_covid_19_time_series/time_series_19-covid-Confirmed.csv"
#URL_DEATHS    = "https://github.com/CSSEGISandData/COVID-19/raw/master/csse_covid_19_data/csse_covid_19_time_series/time_series_19-covid-Deaths.csv"
#URL_RECOVERED = "https://github.com/CSSEGISandData/COVID-19/raw/master/csse_covid_19_data/csse_covid_19_time_series/time_series_19-covid-Recovered.csv"

URL_CONFIRMED = "https://github.com/CSSEGISandData/COVID-19/raw/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_confirmed_global.csv"
URL_DEATHS    = "https://github.com/CSSEGISandData/COVID-19/raw/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_deaths_global.csv"
#URL_RECOVERED = "https://github.com/CSSEGISandData/COVID-19/raw/master/csse_covid_19_data/csse_covid_19_time_series/time_series_19-covid-Recovered.csv"


def get() ->bool:
    try:
        if INDATADIR.exists():
            shutil.rmtree(str(INDATADIR))
        INDATADIR.mkdir(parents=True, exist_ok=True)

        wget.download(URL_CONFIRMED, out=str(LOCAL_CONFIRMED))
        wget.download(URL_DEATHS, out=str(LOCAL_DEATHS))
        #wget.download(URL_RECOVERED, out=str(LOCAL_RECOVERED))
        return True
    except Exception as x:
        LOG.exception(x)
        return False