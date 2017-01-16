#!/usr/bin/python

import os, re, sys, json
import matplotlib.legend_handler as lh
from matplotlib import ticker
import numpy as np

import matplotlib
matplotlib.use('Agg')
import pylab as pl
fig = pl.plt.figure()

################################################

IS_SIM = True

PATH = "../configs"

OUT_DIR = "../plots"

OPTIONS = [
    "tsch-minimal",
    "tsch-dedicated",
    "contikimac",
    "nullrdc",
]

#INTERVALS = [250, 500, 1000, 2000, 4000, 8000, 16000]
INTERVALS = [250, 1000, 4000, 16000]
#INTERVALS = [1000]
#INTERVALS = [4000, 16000]

LABELS = [
    "TSCH minimal",
    "TSCH dedicated",
    "LPL",
    "CSMA"
]

COLORS = [
    "#3388cc",
    "blue",
    "green",
    "red"
]

SAVE_FILES = 1

NUM_TX_NODES = 4

################################################

# regexp helper
class Matcher:
    def __init__(self, pattern, flags=0):
        self._pattern = re.compile(pattern, flags)
        self._hit = None
    def match(self, line):
        self._hit = re.match(self._pattern, line)
        return self
    def search(self, line):
        self._hit = re.search(self._pattern, line)
        return self._hit
    def matched(self):
        return self._hit != None
    def group(self, idx):
        return self._hit.group(idx)
    def as_int(self, idx):
        return int(self._hit.group(idx))

################################################

# cpu listen transmit lpm deep_lpm
POWER_LINE = Matcher(r".*:([0-9]+): [0-9]+ P [0-9]+\.[0-9]+ ([0-9]+) ([0-9]+) ([0-9]+) ([0-9]+) ([0-9]+) ([0-9]+) ([0-9]+) ([0-9]+) ([0-9]+) ([0-9]+) ([0-9]+)$")
POWER_LINE_TESTBED = Matcher(r".* P [0-9]+\.[0-9]+ ([0-9]+) ([0-9]+) ([0-9]+) ([0-9]+) ([0-9]+) ([0-9]+) ([0-9]+) ([0-9]+) ([0-9]+) ([0-9]+) ([0-9]+)$")

#> 361237582:2:LINK STATS to 1: 519 336 6
LINK_STATS_LINE = Matcher(r"> ([0-9]+):([0-9]):LINK STATS to 1: ([0-9]+) ([0-9]+) ([0-9]+)$")
LINK_STATS_LINE_TESTBED = Matcher(r".*> LINK STATS to 1: ([0-9]+) ([0-9]+) ([0-9]+)$")

RX_LINE = Matcher(r"> ([0-9]+):([0-9]):rx ([0-9]): ([0-9]+)$")

TX_LINE = Matcher(r"> ([0-9]+):([0-9]):tx ([0-9]): ([0-9]+)$")


MIN_POWER_SEQNUM = 3
MIN_LINK_STATS_TIME_SEC = 100

################################################

def tsToSeconds(ts):
    if IS_SIM:
        return ts / 1000000.0
    return ts

def isReadable(filename):
    return os.path.isfile(filename) and os.access(filename, os.R_OK)

##########################################
def graphLines(data, filenameOut, xtitle, ytitle):
    pl.figure(figsize=(5, 4))

    for i, option in enumerate(OPTIONS):
        optionData = data[i*len(INTERVALS):(i+1)*len(INTERVALS)]
        optionDataMean = [np.mean(x) for x in optionData]
        optionDataStd = [np.std(x) for x in optionData]
        print(filenameOut, LABELS[i], optionDataMean)
        if "duty" in filenameOut and option == "nullrdc":
            # skip this: always 100%
            continue
        pl.errorbar(range(len(INTERVALS)), optionDataMean, yerr=optionDataStd, width=0.3, label=LABELS[i])

    if "zoomed" in filenameOut:
        pl.ylim(0, 2)
    elif "latency" in filenameOut:
        if 0:
            pl.ylim(ymin = 0)
        else:
            pl.yscale("log")
            pl.ylim(1, 10000)
    elif "prr" in filenameOut:
        pl.ylim(0, 100)
    elif "duty" in filenameOut:
        pl.ylim(0, 15)

    pl.xticks(range(len(INTERVALS)), np.array(INTERVALS)/1000.)
    pl.legend(loc=9, bbox_to_anchor=(0.5, 1.3), ncol=2)

    lpos = (0.0, 0.0)

    pl.grid(True)
    pl.xlabel(xtitle)
    pl.ylabel(ytitle)

    if SAVE_FILES:
        pl.savefig(OUT_DIR + "/" + filenameOut, format='pdf',
                   bbox_inches='tight')
    else:
        pl.show()
    pl.close()

##########################################
def graphBars(data, filenameOut, xtitle, ytitle):
    pl.figure(figsize=(5, 4))

    width = 0.2

    for i, option in enumerate(OPTIONS):
        optionData = data[i*len(INTERVALS):(i+1)*len(INTERVALS)]
        optionDataMean = [np.mean(x) for x in optionData]
        optionDataStd = [np.std(x) for x in optionData]
        x = np.linspace(i * width, len(INTERVALS) + i * width, len(INTERVALS))
        print(filenameOut, LABELS[i], optionDataMean)
        if "duty" in filenameOut and option == "nullrdc":
            # skip this: always 100%
            continue
        pl.bar(x, optionDataMean, yerr=optionDataStd, width=width, label=LABELS[i], color=COLORS[i],
        error_kw = dict(ecolor='black', lw=1, capsize=4, capthick=1))

    if "zoomed" in filenameOut:
        pl.ylim(0, 2)
    elif "latency" in filenameOut:
        if 0:
            pl.ylim(ymin = 0)
        else:
            pl.yscale("log")
            pl.ylim(1, 10000)
            l = [1, 10, 100, 1000, 10000]
            pl.yticks(l, [str(x) for x in l])
    elif "prr" in filenameOut:
        pl.ylim(0, 100)
    elif "duty" in filenameOut:
        pl.ylim(ymin = 0)

    offset = len(INTERVALS) * width / 2.0
    x = np.linspace(offset, len(INTERVALS) + offset, len(INTERVALS))
    pl.xticks(x, ["0.25", "1.0", "4.0", "16.0"])
    pl.legend(loc=9, bbox_to_anchor=(0.5, 1.3), ncol=2)

    lpos = (0.0, 0.0)

    pl.grid(True)
    pl.xlabel(xtitle)
    pl.ylabel(ytitle)

    if SAVE_FILES:
        pl.savefig(OUT_DIR + "/" + filenameOut, format='pdf',
                   bbox_inches='tight')
    else:
        pl.show()
    pl.close()

##########################################

def processFiles(filenames):
    radioOnTicks = {}
    radioTxTicks = {}
    radioListenTicks = {}
    radioTotalTicks = {}
    maxSeqnum = {}
    minSeqnum = {}
    acked = {}
    total = {}
    # (node, seqnum) -> [txTime, rxTime]
    packets = {}

    for filename in filenames:
      with open(filename, "r") as f:
        MIN_PACKET_SEQNUM = 2
        for line in f.readlines():
            line = line.strip()
            m = POWER_LINE.match(line)
            if m.matched():
                node = m.as_int(1)               
                seqnum = m.as_int(2)
                if seqnum >= MIN_POWER_SEQNUM: #  and node != 1:
                    radioOnTicks[node] = radioOnTicks.get(node, 0) + m.as_int(9) + m.as_int(10)
                    radioTxTicks[node] = radioTxTicks.get(node, 0) + m.as_int(10)
                    radioListenTicks[node] = radioListenTicks.get(node, 0) + m.as_int(9)
                    radioTotalTicks[node] = radioTotalTicks.get(node, 0) + m.as_int(8) + m.as_int(11) + m.as_int(12)
                continue
            m = LINK_STATS_LINE.match(line)
            if m.matched():
                #print("link stats", line)
                ts = tsToSeconds(m.as_int(1))
                node = m.as_int(2)
                if ts >= MIN_LINK_STATS_TIME_SEC and node != 1:
                    if m.as_int(4) > m.as_int(3):
                        print("bug!", m.as_int(3), m.as_int(4))
                    total[node] = total.get(node, 0) + m.as_int(3)
                    acked[node] = acked.get(node, 0) + m.as_int(4)
                continue
            m = RX_LINE.match(line)
            if m.matched():
                ts = tsToSeconds(m.as_int(1))
                printingNode = m.as_int(2)
                node = m.as_int(3)
                seqnum = m.as_int(4)
                key = (node, seqnum)
                if key not in packets:
                    packets[key] = [None, ts]
                else:
                    packets[key] = [packets[key][0], ts]
                continue
            m = TX_LINE.match(line)
            if m.matched():
                ts = tsToSeconds(m.as_int(1))
                printingNode = m.as_int(2)
                node = m.as_int(3)
                seqnum = m.as_int(4)
                key = (node, seqnum)
                if key not in packets:
                    packets[key] = [ts, None]
                else:
                    packets[key] = [ts, packets[key][1]]
                if not node in minSeqnum:
                    minSeqnum[node] = seqnum
                maxSeqnum[node] = seqnum
                continue

    result = []

    pdrs = []
    for i in range(NUM_TX_NODES):
        node = i + 2
        missed = 0
        maxSeqnum[node] -= 4 # exclude last 4 packets, which might still be in queue when the xp ends
        for seqnum in range(minSeqnum[node], maxSeqnum[node] + 1):
            key = (node, seqnum)
            if key not in packets or packets[key][1] == None:
                print("missing packet", key, os.path.dirname(filename))
                missed += 1
        expected = maxSeqnum[node] + 1 - minSeqnum[node]
        pdr = 100.0 * (expected - missed) / expected
        pdrs.append(pdr)
    result.append(pdrs)

    prrs = []
    for i in range(NUM_TX_NODES):
        prr = 0.0
        node = i + 2
        if node in total:
            prr = 100.0 * acked[node] / total[node]
        prrs.append(prr)
    result.append(prrs)

    latencies = []
    for i in range(NUM_TX_NODES):
        node = i + 2
        for seqnum in range(minSeqnum[node], maxSeqnum[node] + 1):
            key = (node, seqnum)
            if key in packets and packets[key][1] is not None:
                # rx - tx
                latency = packets[key][1] - packets[key][0]
                if latency < 0:
                    print("bug latency", key, packets[key][1], packets[key][0])
                else:
                    latencies.append(1000.0 * latency)
    result.append(latencies)

    rdcs = []
    rdcsTx = []
    rdcsListen = []
    for i in range(NUM_TX_NODES + 1):
        node = i + 1 # also include the GW
        rdc = 0.0
        rdcTx = 0.0
        rdcListen = 0.0
        if node in radioOnTicks:
            rdc = 100.0 * radioOnTicks[node] / radioTotalTicks[node]
            rdcTx = 100.0 * radioTxTicks[node] / radioTotalTicks[node]
            rdcListen = 100.0 * radioListenTicks[node] / radioTotalTicks[node]
        else:
            print(node, "not in ticks!")
        rdcs.append(rdc)
        rdcsTx.append(rdcTx)
        rdcsListen.append(rdcListen)
    result.append(rdcs)
    result.append(rdcsTx)
    result.append(rdcsListen)

    return result

################################################

def processDirSim(dirname):
    filename = os.path.join(dirname, "COOJA.testlog")
    if not isReadable(filename):
        print("No COOJA.testlog file!")
        return None
    return processFiles([filename])

################################################

def processDirReal(dirname):
    filenames = []
    filename = os.path.join(dirname, "node0.txt")
    if not isReadable(filename):
        print("No BR log file!")
        return None
    filenames.append(filename)
    for i in range(NUM_TX_NODES):
        node = i + 1
        filename = os.path.join(dirname, "node" + str(node) + ".txt")
        if isReadable(filename):
            filenames.append(filename)
        else:
            print("Node log file does not exist:", filename)
    return processFiles(filenames)

################################################

def extractStats(dirname, isSim):
    allResults = []
    for config in  OPTIONS:
        for interval in  INTERVALS:
            subdir = "%s-%u"%(config, interval)
            pathname = os.path.join(dirname, subdir)
            if isSim:
                data = processDirSim(pathname)
            else:
                data = processDirReal(pathname)
            if data:
                allResults.append(data)
    return zip(*allResults)


################################################

def createOutDir(name):
    try:
        os.mkdir(name)
    except:
        pass

################################################

def main():
    createOutDir(OUT_DIR)

    # simulations
    if 0:
        pdr, prr, latency, radioDuty, radioDutyTx, radioDutyListen = extractStats(PATH, isSim = True)

        graphBars(pdr, "cooja_pdr.pdf", "Packet interval, sec", "End-to-end PDR, %")
        graphBars(prr, "cooja_prr.pdf", "Packet interval, sec", "Link-layer PRR, %")
        graphBars(latency, "cooja_latency.pdf", "Packet interval, sec", "Latency, ms")
        # plot only without sink, most often assumed to be mains-powered
        radioDuty = [x[1:] for x in radioDuty]
        graphBars(radioDuty, "cooja_radio_duty.pdf", "Packet interval, sec", "Radio duty cycle, %")
    # real results
    if 1:
        pdr, prr, latency, radioDuty, radioDutyTx, radioDutyListen = extractStats(PATH, isSim = False)

        graphBars(pdr, "cc2650_pdr.pdf", "Packet interval, sec", "End-to-end PDR, %")
        graphBars(prr, "cc2650_prr.pdf", "Packet interval, sec", "Link-layer PRR, %")
        graphBars(latency, "cc2650_latency.pdf", "Packet interval, sec", "Latency, ms")
        # plot only without sink, most often assumed to be mains-powered
        radioDuty = [x[1:] for x in radioDuty]
        graphBars(radioDuty, "cc2650_radio_duty.pdf", "Packet interval, sec", "Radio duty cycle, %")
        print(radioDuty)

###########################################

if __name__ == '__main__':
    main()
    print("all done!")
