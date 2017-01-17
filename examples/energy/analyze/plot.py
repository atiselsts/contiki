#!/usr/bin/python3

import os, sys, time, re, copy, json, datetime, dateutil
import pylab as pl
import matplotlib.legend_handler as lh
import matplotlib.gridspec as gridspec
import matplotlib.patches as patches
import matplotlib.cm as cm
from matplotlib import ticker
import numpy as np

OUT_DIR = "./"

FILENAMES = [
    "rx-tsch.csv",
    "rx-tsch-sec.csv",
    "rx-cmac.csv",
    "rx-cmac-sec.csv",
    "tx-tsch.csv",
    "tx-tsch-sec.csv",
    "tx-cmac.csv",
    "tx-cmac-sec.csv",
]

LABELS = [
    "Rx TSCH, security disabled",
    "Rx TSCH, security enabled",
    "Rx LPL, security disabled",
    "Rx LPL, security enabled",
    "Tx TSCH, security disabled",
    "Tx TSCH, security enabled",
    "Tx LPL, security disabled",
    "Tx LPL, security enabled",
]

SAVE_FILES = 1

SAMPLE_PERIOD_USEC = 43.0 # approximate, empirical

######################################

def pickAt(d, pos):
    start = pos
    end = pos
    while start >= 0 and d[start] > 0:
        start -= 1
    start = max(start, 0)
    while end < len(d) and d[end] > 0:
        end += 1
    print(start, end)
    return d[start:end+1], end + 1

def doFilter(d):
    result = []
    # remove noise
    d = [0 if x < 400 else x for x in d]
    # pick only Tx/Rx regions
    if 0:
        i = 0
        while i < len(d):
            if d[i] >= 10000:
                portion, i = pickAt(d, i)
                result += portion
            else:
                i += 1
    else:
        result = d

    return result

######################################
def plotEnergy(data, indexes, filenameOut):
    pl.figure(figsize=(8, 3))

    for i in indexes:
        d = doFilter(data[i])
        x = np.linspace(0, len(d) - 1, len(d))
        l = LABELS[i]
        if "enabled" in l:
            l = "Security enabled"
        else:
            l = "Security disabled"
        pl.plot([t * SAMPLE_PERIOD_USEC for t in x], [t / 1000.0 for t in d], label=l, lw=2)
        if len(d) < 500:
            pl.xlim(0, 12000)
        else:
            tl = [0, 10000, 20000, 30000, 40000]
            pl.xticks(tl, [str(x) for x in tl])


    pl.ylabel("mA")
    pl.xlabel("Microseconds")
    pl.ylim(0, 20)

    if 0:
        legend = pl.legend(bbox_to_anchor=(0.5, 1.6), loc='upper center', ncol=2,
                           handler_map={lh.Line2D: lh.HandlerLine2D(numpoints=1)})

    if SAVE_FILES:
        if 0:
            pl.savefig(OUT_DIR + "/" + filenameOut, format='pdf',
                       bbox_inches='tight')
        else:
            pl.savefig(os.path.join(OUT_DIR, filenameOut), format='pdf',
                       bbox_inches='tight')
    else:
        pl.show()
    pl.close()


######################################

def readData(filenames):
    result = []
    for i, filename in enumerate(filenames):
        data = np.loadtxt(filename, skiprows=1)
        result.append(data)
        mc = sum(data) / 1000.0
        print(LABELS[i] + ":\t" + str(mc) + " mC\t" + str(mc * 3 / 3600.) + " mWh")
    return result

##########################################

def main():
    data = readData(FILENAMES)
    plotEnergy(data, (0, 1), "energy_rx_tsch.pdf")
    plotEnergy(data, (2, 3), "energy_rx_contikimac.pdf")
    plotEnergy(data, (4, 5), "energy_tx_tsch.pdf")
    plotEnergy(data, (6, 7), "energy_tx_contikimac.pdf")

###########################################

if __name__ == '__main__':
    main()
    print("all done!")
