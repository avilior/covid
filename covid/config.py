from pathlib import Path
import os
from enum import Enum


ROOT = (Path(os.path.dirname(__file__)) / '..').resolve()
INDATADIR = ROOT / "indata/"
LOCAL_CONFIRMED = INDATADIR / "covid19_confirmed.csv"
LOCAL_DEATHS = INDATADIR / "covid19_deaths.csv"
LOCAL_RECOVERED = INDATADIR / "covid19_recovered.csv"
PLOT_DIR = ROOT / "plots"
DB_DIR = ROOT / "db"

OTTAWA_URL = "https://www.ottawapublichealth.ca/en/reports-research-and-statistics/la-maladie-coronavirus-covid-19.aspx"
OTTAWA_HTML_PATH = INDATADIR / "ottawa.html"

class TabulateTableTypes(str, Enum):
    plain="plain"
    simple="simple"
    github="github"
    grid="grid"
    fancy_grid="fancy_grid"
    pipe="pipe"
    orgtbl="orgtbl"
    jira="jira"
    presto="presto"
    pretty="pretty"
    psql="psql"
    rst="rst"
    mediawiki="mediawiki"
    moinmoin="moinmoin"
    youtrack="youtrack"
    html="html"
    latex="latex"
    latex_raw="latex_raw"
    latex_booktabs="latex_booktabs"
    textile="textile"
