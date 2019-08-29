#!/usr/bin/env nix-shell
#!nix-shell -i 'python3.7'

from matplotlib import pyplot as plt
import pandas as pd
import numpy as np
import requests
import re
from datetime import datetime, timedelta
from itertools import repeat
from textwrap import wrap
import matplotlib.dates as mdates

from tools import cache

try:
  from labellines import labelLines
except:
  labelLines = lambda *args, **kwargs: None

http = requests.Session()

urlPrimary = 'https://electionbettingodds.com/DemPrimary2020.html'
urlFinal = 'https://electionbettingodds.com/President2020.html'

WINDOW = '5d'
DATETIME = 'datetime'
MONTH = 1
RANGE = timedelta(days=16 * 7)

DROPOFF_PERCENT = 2

BULLET = '• '

def parseScript(html):
    columnRegex = r"data.addColumn\(\'number\'\, \'(\w+)\'\)"
    columns = [DATETIME]
    for m in re.findall(columnRegex, html):
        columns.append(m)


    dataRegex = r'\[new Date\(([\d\,]+)\)\,([\d\.\,]+\d),?\]'
    rows = []
    for m in re.findall(dataRegex, html):
        date = m[0]
        data = m[1]
        # Because, I kid you not, months are zero-indexed in Javascript. WHY?
        # https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Date#Parameters
        date = [int(n) for n in date.split(',')]
        date[MONTH] += 1
        date = datetime(*date)

        data = [float(x) for x in data.split(',')]
        rows.append([date] + data)

    df = pd.DataFrame(rows, columns=columns)
    df.set_index(DATETIME, inplace=True)
    return df


def getTable(url):
    print(f'Grabbing {url}')
    req = http.get(url)
    raw = req.text
    return parseScript(raw)


def visualise(df, outfile='out.svg'):
    title = f'Chances for winning the presidency for major candidates, given that they win the primary ({WINDOW} rolling mean)'
    title = '\n'.join(wrap(title, 60))
    plt.style.use('fivethirtyeight')

    fig, ax = plt.subplots(figsize=(13.9, 9.84))

    df.plot(title=title, ax=ax, sort_columns=True)

    labelLines(plt.gca().get_lines(), align=False, xvals=repeat(df.index[-1]), clip_on=False, horizontalalignment='left', backgroundcolor='#FFFFFF00')

    plt.axhline(0.5, color='lightgray', linestyle='--') # Mark 50% line

    ax.set_yticklabels(['{:,.0%}'.format(x) for x in ax.get_yticks()])

    ax.xaxis.label.set_visible(False)
    ax.xaxis.set_major_locator(mdates.WeekdayLocator(0))

    fig.tight_layout()

    props = dict(
        boxstyle='round',
        facecolor='white',
        alpha=0.5
    )

    plt.grid(axis='y')
    plt.savefig(outfile)
    plt.close()


@cache(minutes=5)
def main():
    primary = getTable(urlPrimary)
    final = getTable(urlFinal)

    final = final.loc[:, final.iloc[-1] >= DROPOFF_PERCENT]

    inBoth = primary.columns & final.columns
    primary = primary[inBoth]
    final = final[inBoth]

    suffixes = _final, _primary = ['_' + suf for suf in 'primary final'.split()]
    df = pd.merge_asof(primary, final, on=DATETIME, direction='nearest', suffixes=suffixes)
    df.set_index(DATETIME, inplace=True, drop=False)

    for name in inBoth:
        if name == DATETIME:
            continue
        df[name] = df[name+_primary] / df[name+_final]


    df = df[inBoth]
    df.sort_index(axis=1, inplace=True)

    df = df.rolling(WINDOW).mean()

    last_date = df.iloc[-1].name
    cutoff_date = last_date - RANGE

    df = df[df.index >= cutoff_date]

    visualise(df)


if __name__ == '__main__':
    main()
