#!/usr/bin/env nix-shell
#!nix-shell -i 'python3.7'

from matplotlib import pyplot as plt
import pandas as pd
import numpy as np
import requests
import re
from datetime import datetime
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


def visualise(df, outfile='out.png'):
    title = f'Chances for winning the presidency for major candidates, given that they win the primary ({WINDOW} rolling mean)'
    title = '\n'.join(wrap(title, 60))

    fig, ax = plt.subplots(figsize=(9.84, 13.9))

    df.plot(title=title, ax=ax, sort_columns=True)

    labelLines(plt.gca().get_lines(), align=False, xvals=repeat(df.index[-1]), clip_on=False, horizontalalignment='left', backgroundcolor='#FFFFFF00')

    plt.ylim(0, 1)

    vals = np.linspace(0, 1, 20 + 1)
    ax.set_yticks(vals)
    ax.set_yticklabels(['{:,.0%}'.format(x) for x in vals])
    plt.axhline(0.5, color='red', linestyle='--') # Mark 50% line

    ax.xaxis.set_major_locator(mdates.WeekdayLocator(0))
    ax.xaxis.label.set_visible(False)

    fig.tight_layout()

    props = dict(
        boxstyle='round',
        facecolor='white',
        alpha=0.5
    )
    textstr = '\n'.join([
        'How this is calculated:', BULLET + 'https://en.wikipedia.org/wiki/Conditional_probability',
        'Data sources:', BULLET + urlPrimary, BULLET + urlFinal,
        'Source code:', BULLET + 'https://github.com/Synthetica9/ElectionOdds'
    ])

    print(textstr)
    ax.text(0.05, 0.05, textstr, transform=ax.transAxes, fontsize=14,
        verticalalignment='bottom', bbox=props)

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
    visualise(df)


if __name__ == '__main__':
    main()
