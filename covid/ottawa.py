#!/usr/bin/env python3

from bs4 import BeautifulSoup, Tag  #https://www.crummy.com/software/BeautifulSoup/bs4/doc/
import datetime
import itertools

import logging
import math
import matplotlib.pyplot as plt
import pandas as pd
from pandas import Series
from pathlib import Path

import requests
import sys
import typer                     # https://typer.tiangolo.com
from typing import Optional, List
from tabulate import tabulate, tabulate_formats
import click_spinner

from config import OTTAWA_URL, OTTAWA_HTML_PATH, TabulateTableTypes

LOG = logging.getLogger(__name__)

app = typer.Typer()

def getOttawaData(OTTAWA_HTML_PATH : Path) ->Optional[str]:

    LOG.debug(F"Fetching Ottawa HTML page @ {OTTAWA_URL}")
    # TODO put a timeout on the get
    response = requests.get(OTTAWA_URL)
    if response.status_code != 200:
        LOG.warning(F"Error {response.status_code} while fetching: {response.url}")
        return None

    try:
        LOG.debug(F"Saving fetched data to disk at: {OTTAWA_HTML_PATH}")
        with open(str(OTTAWA_HTML_PATH), "w") as outfile:
            outfile.write(response.text)
    except Exception as x:
        LOG.warning(F"Failed to save html data to disk at: {OTTAWA_HTML_PATH}. Error: {x}")
        return None

    LOG.debug(F"Fetched Ottawa raw data from: {OTTAWA_URL}")

    return OTTAWA_HTML_PATH

def parseTable(table: Tag ):
    #print(table)
    data = []
    table_body = table.find('tbody')
    headerRows = table_body.find_all('tr', attrs={'class': 'titlerow'})
    rows = table_body.find_all('tr', attrs={'class': ['row','altrow']})
    for row in rows:
        cols = row.find_all('td')
        cols = [ele.text.strip() for ele in cols]
        #data.append([ele for ele in cols])
        data.append(cols)
    return data


def parseOttawaData(ottawaPath : Path):
    with open(ottawaPath) as fp:
        soup = BeautifulSoup(fp, 'html.parser')

    tables = soup.find_all('table', attrs={'class': 'datatable'})
    newConfirmedRaw = parseTable(tables[0])
    totalConfirmedRaw = parseTable(tables[1])

    result = []
    previousValue = None
    for r in totalConfirmedRaw:
        dt = datetime.datetime.strptime(r[0], '%m/%d/%Y')
        d = F"{dt.year}-{dt.month:02}-{dt.day:02}"
        v = int(r[1])
        if previousValue is not None:
            diff = v - previousValue
        else:
            diff = 0

        previousValue = v
        percentage = 0
        daysToDouble = 99.9  # use this for infinite
        try:
            percentage = 100.00*(diff/v)
            #daysToDouble = math.log10(2)/math.log10(1+percentage/100.0)
        except Exception:
           pass
        try:
            daysToDouble = round(math.log10(2) / math.log10(1 + percentage / 100.0))
        except Exception:
            pass

        result.append((d,v,diff,percentage,daysToDouble))
    return result



@app.command(help="Generate table using Ottawa data")
def table(tableformat: TabulateTableTypes = TabulateTableTypes.simple, file:Path = typer.Argument(None, file_okay=True,resolve_path=True,)):

    ottawaPath = OTTAWA_HTML_PATH

    data = parseOttawaData(ottawaPath)

    if file:
        pass
    else:

        print(F"\nData for Ottawa as of {data[-1][0]}\n")
        print(tabulate(data,headers=["num","date","total","new","%growth","days to\ndouble"], showindex=range(1, len(data)+1), floatfmt=".01f", tablefmt=tableformat))

@app.command(help="Generate plots for Ottawa data at the optional path. If a path is not specified the plot is displayed interactively using matplotlib.")
def plot(movingaverage:int = None, file:Path = typer.Argument(None, file_okay=True,resolve_path=True,)):

    ottawaPath = OTTAWA_HTML_PATH

    data = parseOttawaData(ottawaPath)

    dates = [r[0] for r in data]
    totalCases = [r[1] for r in data]
    newCases = [r[2] for r in data]
    percentage = [r[3] for r in data]
    doubling   = [r[4] for r in data]

    totalCasesMovingAverage = None
    newCasesMovingAverage = None

    if movingaverage:
        totalCasesMovingAverage = (pd.Series(totalCases).rolling(window=movingaverage).mean().iloc[:].values).tolist()
        newCasesMovingAverage = (pd.Series(newCases).rolling(window=movingaverage).mean().iloc[:].values).tolist()

    fig, axs = plt.subplots(1, 4, figsize=(18, 8))

    plt.suptitle(f'Ottawa {dates[-1]}\n', y=1.05, weight="bold")

    axs[0].set_title(f"Total cases,\n..., {totalCases[-3]}, {totalCases[-2]}, {totalCases[-1]}")
    axs[0].set_ylabel(f"Infected")
    axs[0].plot(totalCases, c="black")
    if totalCasesMovingAverage:
        axs[0].plot(totalCasesMovingAverage, c="grey")


    axs[1].set_title(f"New cases,\n..., {newCases[-3]}, {newCases[-2]}, {newCases[-1]}")
    axs[1].set_ylabel(f"Newly Infected")
    axs[1].plot(newCases, c="red")

    if newCasesMovingAverage:
     axs[1].plot(newCasesMovingAverage, c="pink")


    axs[2].set_title(f"Percentage,\n..., {percentage[-3]:.0f}%, {percentage[-2]:.0f}%, {percentage[-1]:.0f}%")
    axs[2].set_ylabel(f"Percentage growth")
    axs[2].plot(percentage, c="green")

    axs[3].set_title(f"Days to double,\n..., {doubling[-3]:.01f}, {doubling[-2]:.01f}, {doubling[-1]:.01f}")
    axs[3].set_ylabel(f"Days")
    axs[3].plot(doubling, c="green")

    axs[0].grid(True)
    axs[1].grid(True)
    axs[2].grid(True)
    axs[3].grid(True)

    plt.tight_layout()

    if file:
        # if the file is a directory then generate a file name
        if file.is_dir():
            file = file / F"{dates[-1]}-ottawa.png"

        plt.tight_layout()
        plt.savefig(str(file), bbox_inches='tight')
        plt.close()
        typer.echo(F"Saved plot: {file}")
    else:
        plt.show()

# This is the main application: add CLI Parameters for the main CLI Application herSKIP_FETCHING_HTML = False

SKIP_FETCHING_HTML = False

@app.callback()
def main(ctx: typer.Context):
    """
        This CLI processes Ottawa data using the Ottawa PHU data:

        - loads the data locally

        - creates plots
    """
    LOG.debug(F"OTTAWA: command path: {ctx.command_path}")
    LOG.debug(F"OTTAWA: executing sub command: {ctx.invoked_subcommand}")

    # NOTE: this code will get executed even when we do covid ottawa table --help
    if not SKIP_FETCHING_HTML:
        typer.echo("Loading data from website...  ",nl=False)
        with click_spinner.spinner():
            ottawaPath = getOttawaData(OTTAWA_HTML_PATH)
        typer.echo("     DONE")
        if ottawaPath is None:
            return -1

if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s,%(msecs)d %(levelname)s: %(message)s',
        datefmt='%H:%M:%S'
    )
    app()
