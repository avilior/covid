import datetime
import logging
from pathlib import Path
import pandas as pd
from pandas import DataFrame, Series
import numpy as np
import matplotlib.pyplot as plt



import json
from us_state_abbreviation import us_state_abbrev

from config import ROOT, INDATADIR, LOCAL_CONFIRMED, LOCAL_DEATHS, LOCAL_RECOVERED, PLOT_DIR, DB_DIR
LOG = logging.getLogger(__name__)

DB = {}

def store(*, country:str ,province:str = None, city: str = None, confirmed:list = None,  death:list = None ):

    if country is None:
        LOG.warning(F"store requires country to be specified. Country was NONE")
        return
    if confirmed is None or len(confirmed) == 0:
        LOG.warning(F"store requires confirmed data to be specified. confirmed data was NONE or EMPTY")
        return


    if death is None or len(death) == 0:
        LOG.warning(F"store requires death data to be specified. death data was NONE or EMPTY")
        return

    country = country.strip()
    country_record = DB.setdefault(country,{ "name" : country, "confirmed" : confirmed, "death": death, "provinces": { } } )
    if province is None:

        country_record["confirmed"] = confirmed
        country_record["death"] = death
        return

    province_name = province.strip()
    province = province_name
    if country == 'US':
        province = us_state_abbrev.get(province.lower(), province_name)

    province_record = country_record["provinces"].setdefault(province, {"name": province_name, "confirmed":confirmed, "death": death, "cities" : {}})
    if city is None:
        province_record["confirmed"] = confirmed
        province_record["death"] = death
        return

    city = city.strip()
    city_record = province_record["cities"].setdefault(city, {"name": city, "confirmed":confirmed, "death": death })
    city_record["confirmed"] = confirmed
    city_record["death"] = death

def doPlot(title, titlePreamble, data, diff, percent):

    fig, axs = plt.subplots(1, 3, figsize=(18, 8))

    plt.suptitle(f'{title}\n', y=1.05, weight="bold")

    axs[0].set_title(f"Total cases,\n..., {data[-3]}, {data[-2]}, {data[-1]}")
    axs[0].set_ylabel(f"Infected")
    axs[0].plot(data, c="black")

    axs[1].set_title(f"New cases,\n..., {diff[-3]}, {diff[-2]}, {diff[-1]}")
    axs[1].set_ylabel(f"Newly Infected")
    axs[1].plot(diff, c="red")

    axs[2].set_title(f"Percentage,\n..., {np.round(percent[-3], 1)}, {np.round(percent[-2], )}, {np.round(percent[-1], )}")
    axs[2].set_ylabel(f"Percentage growth")
    axs[2].plot(percent, c="green")

    axs[0].grid(True)
    axs[1].grid(True)
    axs[2].grid(True)

    # plt.show()
    plotfilepath = PLOT_DIR / F"{titlePreamble}-{title}.png"
    plt.tight_layout()
    plt.savefig(str(plotfilepath), bbox_inches='tight')
    plt.close()


def computeFromRow(row:Series):

    data = row[4:].to_numpy()
    diff = np.diff(data, 1)
    percent = 100 * np.divide(diff, data[1:], out=np.zeros_like(diff), where=data[1:] != 0)

    return data, diff, percent

def doRows(confirmed: pd.DataFrame, death: pd.DataFrame):

    for index, row in  confirmed.iterrows():
        try:
            #print(F"index: {index} row: {row}")

            # get the date of the last column - we will use that as the timestamp
            colName = row.index[-1]
            dt = datetime.datetime.strptime(colName, '%m/%d/%y')

            titlePreamble = F"{dt.year}{dt.month:02}{dt.day:02}"
            # we want to skip over cities
            province = row[0]
            country  = row[1]

            # get the rows from the other data frame

            death_row = death[death['Country/Region'] == country]
            if isinstance(province, str):
                death_row = death_row[death_row['Province/State'] == province]

            isProvince = False
            isCountryOnly = False
            if isinstance(province, str):
                isProvince = province.find(",") == -1
            else:
                isCountryOnly = True

            if isCountryOnly:
                title = country
                province, city = None, None
            elif isProvince:
                title = F"{country}_{province}"
                city = None
            else:
                city, province = province.split(",",1)
                title = F"{country}_{province}_{city}"

            LOG.info(F"{country} {province} {city}")

            lat, lon = row[2:4]
            # get the data as a numpy array

            confirmed_data, confirmed_diff, confirmed_percent = computeFromRow(row)

            x = death_row.iloc[0]
            death_data, death_diff, death_percent = computeFromRow(x)

            doPlot(title, titlePreamble, confirmed_data, confirmed_diff, confirmed_percent)

            c = confirmed_data.astype(np.int32)
            d = death_data.astype(np.int32)


            if isCountryOnly:
                store(country=country,province = None, city = None, confirmed = c.tolist(),  death=d.tolist())
            else:
                store(country = country, province=province, city=city, confirmed=c.tolist(), death=d.tolist() )
        except Exception as x:
            LOG.warning(F"While processing country: {country} province: {province} got exception: {x}")


def compute(data):

    if data is not None:
        data = np.sum(data[:, 4:], axis=0)
        data = data[np.newaxis, :]
        diff = np.diff(data[0, 4:], 1)
        percent = 100 * np.divide(diff, data[0, 5:], out=np.zeros_like(diff), where=data[0, 5:] != 0)

        return data, diff, percent
    return None, None, None

def extract(country, df):

    if df is None:
        raise Exception("Dataframe is none")

    if country == "US": # us is special because it reports cities
        df = df[df['Province/State'].str.contains(",") == False]

    province = None
    city     = None
    LOG.info(F"{country} {province} {city}")


    # get the last column name of the dataframe so we can create the timestamp for the filename
    colName = list(df.columns)[-1]
    dt = datetime.datetime.strptime(colName, '%m/%d/%y')

    titlePreamble = F"{dt.year}{dt.month:02}{dt.day:02}"

    data = df.to_numpy()

    return country, province, city, titlePreamble, data

def doCountry(country: str, df_confirmed : DataFrame, df_death : DataFrame):

    LOG.info(F"Processing country: {country}")

    df_confirmed_country = df_confirmed[df_confirmed['Country/Region'] == country]
    df_death_country = df_death[df_death['Country/Region'] == country]

    country, province, city, titlePreamble, confirmed = extract(country, df_confirmed_country)
    countryD, provinceD, cityD, titlePreambleD, death = extract(country,  df_death_country)

    confirmed, confirmed_diff, confirmed_percent = compute(confirmed)
    death, death_diff, death_percent = compute(death)

    doPlot(country, titlePreamble, confirmed[0,:], confirmed_diff, confirmed_percent)
    store(country=country,province=province,city=city,confirmed=list(confirmed[0,:]),death=list(death[0,:]))


def process():
    df_confirmed = pd.read_csv(LOCAL_CONFIRMED)
    df_death     = pd.read_csv(LOCAL_DEATHS)

    # create an array of the dates in the data.  column 4 is the start of the data
    dts = [datetime.datetime.strptime(cn, '%m/%d/%y') for cn in list(df_confirmed.columns.values)[4:]]
    dts = [F"{d.year}-{d.month:02}-{d.day:02}" for d in dts]

    DB['metadata'] = { 'start' : dts[0], "end": dts[-1], "dates" : dts}

    doCountry("Canada", df_confirmed, df_death)
    # no longer needed doCountry("US", df_confirmed, df_recovered, df_death)
    doCountry("China", df_confirmed, df_death)
    doCountry("Australia", df_confirmed, df_death)
    doRows(df_confirmed, df_death)

    if not DB_DIR.exists():
        DB_DIR.mkdir(parents=True, exist_ok=True)

    DB_PATH = DB_DIR / "db.json"

    with open(DB_PATH, "w") as dbfile:
        json.dump(DB, dbfile, indent=2)

    LOG.info("DONE")

    return
