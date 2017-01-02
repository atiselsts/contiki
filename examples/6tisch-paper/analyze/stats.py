#!/usr/bin/python

import os, re, sys, json
import pylab as pl
import matplotlib.legend_handler as lh
from matplotlib import ticker
import numpy as np

################################################

IS_SIM = True

PATH = "../configs"

OUT_DIR = "../plots"

OPTIONS = [
    "tsch-fast",
    "tsch-slow",
    "contikmac-fast",
    "contikmac-slow",
    "nullrdc",
]

LABELS = [
    "TSCH min-5",
    "TSCH min-13",
    "ContikiMAC 64 Hz",
    "ContikiMAC 8 Hz",
    "Always on"
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
POWER_LINE = Matcher(r".*:([0-9]): [0-9]+ P [0-9]+\.[0-9]+ ([0-9]+) ([0-9]+) ([0-9]+) ([0-9]+) ([0-9]+) ([0-9]+) ([0-9]+) ([0-9]+) ([0-9]+) ([0-9]+) ([0-9]+)$")
POWER_LINE_TESTBED = Matcher(r".* P [0-9]+\.[0-9]+ ([0-9]+) ([0-9]+) ([0-9]+) ([0-9]+) ([0-9]+) ([0-9]+) ([0-9]+) ([0-9]+) ([0-9]+) ([0-9]+) ([0-9]+)$")

#> 361237582:2:LINK STATS to 1: 519 336 6
LINK_STATS_LINE = Matcher(r"> ([0-9]+):([0-9]):LINK STATS to 1: ([0-9]+) ([0-9]+) ([0-9]+)$")
LINK_STATS_LINE_TESTBED = Matcher(r".*> LINK STATS to 1: ([0-9]+) ([0-9]+) ([0-9]+)$")

RX_LINE = Matcher(r"> ([0-9]+):([0-9]):rx ([0-9]): ([0-9]+)$")

TX_LINE = Matcher(r"> ([0-9]+):([0-9]):tx ([0-9]): ([0-9]+)$")


MIN_POWER_SEQNUM = 3
MIN_LINK_STATS_TIME_SEC = 100
MIN_PACKET_SEQNUM = 18 # 3 min to establish
MAX_PACKET_SEQNUM = 50

################################################

def tsToSeconds(ts):
    if IS_SIM:
        return ts / 1000000.0
    return ts

def isReadable(filename):
    return os.path.isfile(filename) and os.access(filename, os.R_OK)

##########################################
def graphBoxes(data, filenameOut, xtitle, ytitle):
    pl.figure(figsize=(5, 4))

    width = 0.5

    boxprops = dict(linewidth=1, color="black")
    flierprops = dict(marker='o', markersize=3, fillstyle="none")
#                      markeredgewidth=2, linestyle='none', color="black")
    medianprops = dict(linewidth=1)
    lineprops = dict(linewidth=2, color="black")

    if "zoomed" in filenameOut:
        pl.ylim(0, 2)
    elif "prr" in filenameOut:
        pl.ylim(0, 100)
    elif "duty" in filenameOut:
        pl.ylim(0, 6)

    pl.boxplot(data, labels=LABELS[:len(data)],
               widths=width,
               boxprops=boxprops, flierprops=flierprops,
               medianprops=medianprops, meanprops=lineprops,
               whiskerprops=lineprops, capprops=lineprops)

#    pl.xticks(range(-1, len(LABELS)), LABELS + [""], rotation= 45)
    pl.xticks(rotation= 90)

    lpos = (0.0, 0.0)

    pl.xlabel(xtitle)
    pl.ylabel(ytitle)

    if SAVE_FILES:
        if 1:
            pl.savefig(OUT_DIR + "/" + filenameOut, format='pdf',
#                       bbox_extra_artists=(legend,),
                       bbox_inches='tight')
        else:
            filenameOut = filenameOut.replace("pdf", "png")
            pl.savefig(os.path.join(OUT_DIR, filenameOut), format='png',
#                       bbox_extra_artists=(legend,),
                       bbox_inches='tight')
    else:
        pl.show()
    pl.close()


##########################################

def processFiles(filenames):
    radioOnTicks = {}
    radioTotalTicks = {}
    acked = {}
    total = {}
    # (node, seqnum) -> [txTime, rxTime]
    packets = {}

    for filename in filenames:
      with open(filename, "rb") as f:
        for line in f.readlines():
            line = line.strip()
            m = POWER_LINE.match(line)
            if m.matched():
                node = m.as_int(1)
                seqnum = m.as_int(2)
                if seqnum >= MIN_POWER_SEQNUM: #  and node != 1:
                    radioOnTicks[node] = radioOnTicks.get(node, 0) + m.as_int(9) + m.as_int(10)
                    radioTotalTicks[node] = radioTotalTicks.get(node, 0) + m.as_int(7) + m.as_int(8) + m.as_int(11)
                continue
            m = LINK_STATS_LINE.match(line)
            if m.matched():
                #print("link stats", line)
                ts = tsToSeconds(m.as_int(1))
                node = m.as_int(2)
                if ts >= MIN_LINK_STATS_TIME_SEC and node != 1:
                    total[node] = total.get(node, 0) + m.as_int(3)
                    acked[node] = acked.get(node, 0) + m.as_int(4)
                continue
            m = RX_LINE.match(line)
            if m.matched():
                ts = tsToSeconds(m.as_int(1))
                printingNode = m.as_int(2)
                node = m.as_int(3)
                seqnum = m.as_int(4)
                if seqnum >= MIN_PACKET_SEQNUM:
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
                if seqnum >= MIN_PACKET_SEQNUM:
                    key = (node, seqnum)
                    if key not in packets:
                        packets[key] = [ts, None]
                    else:
                        packets[key] = [ts, packets[key][1]]
                continue

    result = []

    pdrs = []
    for i in range(NUM_TX_NODES):
        node = i + 2
        missed = 0
        for seqnum in range(MIN_PACKET_SEQNUM, MAX_PACKET_SEQNUM + 1):
            key = (node, seqnum)
            if key not in packets:
                print("missing packet", key, filename)
                missed += 1
        expected = MAX_PACKET_SEQNUM + 1 - MIN_PACKET_SEQNUM
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
        for seqnum in range(MIN_PACKET_SEQNUM, MAX_PACKET_SEQNUM + 1):
            key = (node, seqnum)
            if key in packets and packets[key][1] is not None:
                # rx - tx
                latency = packets[key][1] - packets[key][0]
                latencies.append(latency)
    result.append(latencies)

    rdcs = []
    for i in range(NUM_TX_NODES + 1):
        node = i + 1 # also include the GW
        rdc = 0.0
        if node in radioOnTicks:
            rdc = 100.0 * radioOnTicks[node] / radioTotalTicks[node]
        else:
            print(node, "not in ticks!")
        rdcs.append(rdc)
    result.append(rdcs)

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
    filename = os.path.join(dirname, "br/node1.txt")
    if not isReadable(filename):
        print("No BR log file!")
        return None
    filenames.append(filename)
    for i in range(NUM_TX_NODES):
        node = i + 2
        filename = os.path.join(dirname, "node/node" + str(node) + ".txt")
        if isReadable(filename):
            filenames.append(filename)
        else:
            print("Node log file does not exist:", filename)
    return processFiles(filenames)

################################################

def extractStatsTestbed(dirname):
    MIN_PACKETS = 59

    pdr = []
    per = []
    duty = []

    print(dirname)

    for n in NODES:
      node = int(n)

      prrTotal = 0
      prrAcked = 0
      radioOnTicks = 0
      radioTotalTicks = 0

      hasJoinedTsch = True if node == 1 else False
      hasValidLinkStats = True if node == 1 else False

      filename = os.path.join(dirname, "node" + n + "-log.log--2016-10-25")
      with open(filename, "rb") as f:
        for line in f.readlines():
            line = line.strip()
            m = POWER_LINE_TESTBED.match(line)
            if m.matched():
                seqnum = m.as_int(1)
                #print("powertrace", node, lastSeqnum)
                if not hasJoinedTsch:
                    # not joined yet; ignore the stats in this case
                    pass
                elif hasValidLinkStats:
                    radioOnTicks += m.as_int(8) + m.as_int(9)
                    radioTotalTicks += m.as_int(7) + m.as_int(10) + m.as_int(11)
                continue
            m = LINK_STATS_LINE_TESTBED.match(line)
            if m.matched():
                hasValidLinkStats = False
                # do this only when the network is stable
                if hasJoinedTsch:
                    total = m.as_int(1)
                    acked = m.as_int(2)
                    if total < MIN_PACKETS:
                        print("Ignoring link stats: no data connection yet")
                        pass
                    elif acked == 0:
                        print("Bogus link stats: no packets acked")
                        pass
                    else:
                        prrTotal += total
                        prrAcked += acked
                        hasValidLinkStats = True
                continue
            m = TSCH_JOIN_LINE_TESTBED.match(line)
            if m.matched():
                hasJoinedTsch = True
                continue
      if node != 1:
          per.append(100 - (100 * prrAcked / float(prrTotal)))
      duty.append(100 * radioOnTicks / float(radioTotalTicks))

    print("per=", per, "avg=", 1.0 * sum(per) / len(per))
    print("duty=", duty, "avg=", 1.0 * sum(duty) / len(duty))
    return pdr, per, duty

################################################
          
def extractStats(dirname, isSim):
    allResults = []
    for subdir in  OPTIONS:
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
    global NUM_TX_NODES
    global MAX_PACKET_SEQNUM
    
    createOutDir(OUT_DIR)

    pdr, prr, latency, radioDuty = extractStats(PATH, isSim = True)

    graphBoxes(pdr, "cooja_pdr.pdf", "Protocol", "End-to-end PDR, %")
    graphBoxes(prr, "cooja_prr.pdf", "Protocol", "Link-layer PRR, %")
    graphBoxes(latency, "cooja_latency.pdf", "Protocol", "Latency, sec")
    graphBoxes(latency, "cooja_latency_zoomed.pdf", "Protocol", "Latency, sec")
    radioDuty = radioDuty[:-1]  # not intereseted in 100%
    graphBoxes(radioDuty, "cooja_radio_duty.pdf", "Protocol", "Radio duty cycle, %")
    radioDuty = [x[1:] for x in radioDuty]
    graphBoxes(radioDuty, "cooja_radio_duty_without_sink.pdf", "Protocol", "Radio duty cycle, %")

    NUM_TX_NODES = 1
    MAX_PACKET_SEQNUM = 60
    pdr, prr, latency, radioDuty = extractStats(PATH, isSim = False)

    graphBoxes(pdr, "cc2538_pdr.pdf", "Protocol", "End-to-end PDR, %")
    graphBoxes(prr, "cc2538_prr.pdf", "Protocol", "Link-layer PRR, %")
    graphBoxes(latency, "cc2538_latency.pdf", "Protocol", "Latency, sec")
    graphBoxes(latency, "cc2538_latency_zoomed.pdf", "Protocol", "Latency, sec")
    radioDuty = radioDuty[:-1]  # not intereseted in 100%
    graphBoxes(radioDuty, "cc2538_radio_duty.pdf", "Protocol", "Radio duty cycle, %")
    radioDuty = [x[1:] for x in radioDuty]
    graphBoxes(radioDuty, "cc2538_radio_duty_without_sink.pdf", "Protocol", "Radio duty cycle, %")
    

###########################################

if __name__ == '__main__':
    main()
    print("all done!")
