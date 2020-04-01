#!/usr/bin/env python3

"""
  covid
       world
           getData
           covid
           report
              table
              plot
       ottawa
"""
import logging
import typer                     # https://typer.tiangolo.com
import getData
import processWorld
import click_spinner
import report

LOG = logging.getLogger("covid")

app = typer.Typer()

app.add_typer(report.app, name="report")

@app.command(help="Get raw covid-19 data from john hopkins")
def load() -> None:
    typer.echo("Loading data from website...  ", nl=False)
    with click_spinner.spinner():
        getData.get()
    typer.echo("   DONE ")

@app.command(help="Process world data creating db and plots")
def process() -> None:
    processWorld.process()

# This is the main application: add CLI Parameters for the main CLI Application her
@app.callback()
def main(ctx: typer.Context):
    """
        This CLI processes world covid data using the John Hopkins data set:
        loads the data locally
        creates plots
    """
    LOG.debug(F"COVIDAP: executing command: {ctx.invoked_subcommand}")

######################


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s,%(msecs)d %(levelname)s: %(message)s',
        datefmt='%H:%M:%S'
    )
    app()