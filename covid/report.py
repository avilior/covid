#!/usr/bin/env python3

from typing import Optional, List
import logging
import typer                     # https://typer.tiangolo.com
from config import DB_DIR
import json
import matplotlib.pyplot as plt
from pathlib import Path
from tabulate import tabulate    # https://pypi.org/project/tabulate/
import math

LOG = logging.getLogger(__name__)
DB_PATH = DB_DIR / "db.json"

app = typer.Typer()

headers = ["idx", "Country", "Max", "Max-Day", "Today", "Deaths", "%Deaths", F"Last", "New Cases", "%growth", "Double\nDays"]

COL_PERCENT_DEATHS = headers.index("%Deaths") - 1
COL_LAST           = headers.index("Last") - 1
COL_NEW_CASES      = headers.index("New Cases") - 1
COL_PERCENT_GROWTH = headers.index("%growth") - 1
COL_DOUBLE_DAYS    = headers.index("Double\nDays") - 1


def __loadDB() -> Optional[dict]:
    DB = None
    if not DB_DIR.exists():
        LOG(F"Cant find DB dir {DB_DIR}")
    else:
        try:
            with open(DB_PATH, "r") as dbfile:
                LOG.debug(F"Found db file: {DB_PATH}")
                DB = json.load(dbfile)
                LOG.debug("Loaded db")
        except Exception as x:
            LOG.info(F"Failed to parse DB: {x}")
    return DB

def _array2String(r):
    r = list(r)

    r[COL_LAST]           = ','.join([F"{s:>7}" for s in r[COL_LAST]])
    r[COL_NEW_CASES]      = ','.join([F"{s:>7}" for s in r[COL_NEW_CASES]])
    r[COL_PERCENT_GROWTH] = ', '.join([F"{s:>2.0f}" for s in r[COL_PERCENT_GROWTH]])
    r[COL_DOUBLE_DAYS]    = ', '.join([F"{s:>3.0f}" for s in r[COL_DOUBLE_DAYS]])
    return tuple(r)

@app.command()
def table( sort_col:str = typer.Option("Max", help="Select the column name to sort on"),
           days:int = typer.Option(3, help="Show the last N days and N-1 New Cases"),
           rows:int = typer.Option(0, help="The number of table rows to display")) :
    """
    Find country with the highest number of cases
    """
    DB = __loadDB()

    result = []
    length = 0


    for country, record in DB.items():
        confirmed = record.get("confirmed",None)
        deaths    = record.get("death", None)
        if not confirmed:
            LOG.info(F"Country {country} has no data")
            continue
        length = max(length, len(confirmed))
        today_cases = confirmed[-1]
        today_death = deaths[-1]

        try:
            percentDeaths = F"{100*today_death/today_cases:.0f}"
        except ZeroDivisionError:
            percentDeaths = "NaN"

        max_cases = max(confirmed)
        day_index = 1 + confirmed.index(max_cases)

        cases = confirmed[-days:]
        diff = [cases[i + 1] - cases[i] for i in range(0, len(cases) - 1)]
        percent = [ 100*(diff[i] / cases[i]) for i in range(0, len(diff)) if cases[i] != 0]
        days_double = [ math.log10(2)/math.log10(1 + p/100.0) for p in percent if p != 0 ]

        result.append((country, max_cases, day_index, today_cases, today_death, percentDeaths, cases, diff, percent, days_double))

    try:
        sort_col_index = headers.index(sort_col)
    except:
        LOG.warning(F"Sort_col should match one of the following column names: {headers[1:]} defaulting to Max")
        sort_col_index = 1

    sortKey = sort_col_index - 1
    if sortKey == COL_NEW_CASES:
        result.sort(key=lambda tup: tup[sortKey][-1], reverse=True)
    else:
        result.sort(key=lambda tup: tup[sortKey], reverse=True)  # sorts in place

    #result.append((country, max_cases, day_index, today_cases, ' '.join([str(s) for s in cases]), ' '.join([str(s) for s in diff])))

    result = list(map(_array2String, result))

    if rows > 0:
        result = result[:rows]

    headers[sort_col_index] = headers[sort_col_index] + "*"
    headers[7] = headers[7] + F" {days} days"
    headers[7] = headers[7] + "\n"

    for i in range(-days+1,1):
        headers[7] = headers[7] + F"{i}      "

    headers[8] = headers[8] + "\n"
    for i in range(-days+2,1):
        headers[8] = headers[8] + F"{i}      "

    numberOfRows = str(rows) if rows != 0 else "all rows"
    print(F"From date: {DB['metadata']['start']} to date: {DB['metadata']['end']}")
    print(F"Sort column: {sort_col} Number of Rows: {numberOfRows}")
    print("")
    print(tabulate(result,headers=headers, showindex=range(1, len(result)+1), floatfmt="0f"))

# file:Path = typer.Argument(None, file_okay=True,resolve_path=True,)
@app.command()
#def plot(countries: List[str], save : bool = typer.Option(False, help="save the plot using plot.png at the local directory")):
def plot(countries: List[str], file : Path = typer.Option(None, file_okay=True,resolve_path=True, help="save the plot at the specified directory or specified file")):

    """
    Plot confirmed cases and death of one or more countries.
    Each series begins when the first confirmation is reported.
    """

    DB = __loadDB()

    result = []

    for country in countries:
        record = DB.get(country, None)

        if record is None:
            print(F"Country: {country} not found")
            continue

        confirmed = record["confirmed"]
        death    = record["death"]
        firstNoneZero = confirmed.index(next(filter(lambda x: x > 0, confirmed)))
        confirmed = confirmed[firstNoneZero :]
        firstNoneZero = death.index(next(filter(lambda x: x > 0, death)))
        death = death[firstNoneZero:]


        result.append((country, confirmed, death))

    fig, axs = plt.subplots(1, 2, figsize=(9, 4))
    plt.suptitle(f"Compare {DB['metadata']['end']}", y = 1.05, weight="bold")

    axs[0].set_title(f"Confirmed Cases")
    axs[0].set_ylabel(f"Infected")
    axs[0].set_xlabel("Days Since Country's First Case")
    axs[1].set_title(f"Deaths")
    axs[1].set_ylabel(f"Deaths")
    axs[1].set_xlabel("Days Since Country's First Death")
    for d in result:
        axs[0].plot(d[1], label=d[0])
        axs[1].plot(d[2], label=d[0])


    axs[0].legend(loc='upper left')
    axs[1].legend(loc='upper left')
    axs[0].grid(True)
    axs[1].grid(True)

    # plt.yscale('log')
    # plt.xscale('log')

    plt.tight_layout()
    if file:
        if file.is_dir():
            # sort the countries join them with '_' and replace spaces with '-'
            countries_string = '_'.join(sorted(countries)).replace(' ','-')
            #countries_string = countries_string.replace(' ','-')

            endDate = DB['metadata']['end']
            file = file / F"{endDate}_{countries_string}.png"

        plt.tight_layout()
        plt.savefig(str(file), bbox_inches='tight')
    plt.show()

# This is the main application: add CLI Parameters for the main CLI Application her
@app.callback()
def main(ctx: typer.Context):
    """
        This CLI generates reports:

        - report for countries

        - plots comparing countries
    """
    LOG.debug(F"COVIDAP: executing command: {ctx.invoked_subcommand}")

if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s,%(msecs)d %(levelname)s: %(message)s',
        datefmt='%H:%M:%S'
    )
    app()
