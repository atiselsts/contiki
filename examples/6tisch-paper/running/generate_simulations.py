#!/usr/bin/python

import os, copy

OUT_DIRECTORY="../configs"

########################################

def createOutDir(name):
    try:
        os.mkdir(name)
    except:
        pass

def touch(fname, times=None):
    with open(fname, 'a'):
        os.utime(fname, times)

def link(dirname, filename):
    targetName = os.path.join("../..", filename)
    if "/" in filename:
        targetName = os.path.join("..", targetName)
    filename = os.path.join(dirname, filename)
    try:
        os.remove(filename)
    except:
        pass
    try:
        os.symlink(targetName, filename)
    except:
        pass

def rm(dirname, filename):
    filename = os.path.join(dirname, filename)
    try:
        os.remove(filename)
    except:
        pass

def generateSimulation(makefileTemplate, simTemplate, variables, dirname):
    createOutDir(dirname)
    createOutDir(os.path.join(dirname, "br"))
    createOutDir(os.path.join(dirname, "node"))

    mt = copy.copy(makefileTemplate)
    st = copy.copy(simTemplate)
    for key in variables:
        mt = mt.replace("@" + key + "@", str(variables[key]))
        st = st.replace("@" + key + "@", str(variables[key]))

    filename = os.path.join(dirname, "Makefile.common")
    with open(filename, "w") as outFile:
        outFile.write(mt)

    filename = os.path.join(dirname, "sim.csc")
    with open(filename, "w") as outFile:
        outFile.write(st)

    link(dirname, "br/node.c")
    link(dirname, "br/Makefile")
    link(dirname, "br/project-conf.h")
    link(dirname, "node/node.c")
    link(dirname, "node/Makefile")
    link(dirname, "node/project-conf.h")
    link(dirname, "common-conf.h")
    rm(dirname, "log.log")
    rm(dirname, "COOJA.log")
    rm(dirname, "COOJA.testlog")
 

def generateOptions(outDir, dirname, variables):
    outDir = os.path.join(outDir, dirname)
    createOutDir(outDir)

    makefileTemplate = open("Makefile.template", "r").read()
    simTemplate = open("sim.csc.template", "r").read()

    generateSimulation(makefileTemplate, simTemplate, variables, outDir)



# default: no slot reappropriation, MRHOF routing function
variables = {
    "USE_TSCH" : 0,
    "USE_TSCH_WITH_DEDICATED_SLOTS" : 0,
    "USE_NULLRDC" : 0,
    "PACKETGEN_PERIOD_MILLISECONDS" : 500,
    "NETSTACK_CONF_RDC_CHANNEL_CHECK_RATE" : 8,
    "TSCH_SCHEDULE_CONF_DEFAULT_LENGTH" : 7,
    "DEF_LEAVES_COUNT" : 4,
    "DEF_STARTUP_DELAY" : 5 * 60, # give some time for TSCH to sync and learn drift
}

def main():
    createOutDir(OUT_DIRECTORY)

    for interval in [250, 500, 1000, 2000, 4000, 8000, 16000]:
        v = copy.copy(variables)
        v["USE_TSCH"] = 1
        v["TSCH_SCHEDULE_CONF_DEFAULT_LENGTH"] = 13
        v["PACKETGEN_PERIOD_MILLISECONDS"] = interval
        generateOptions(OUT_DIRECTORY, "tsch-minimal-%u"%(interval), v)

        v = copy.copy(variables)
        v["USE_TSCH"] = 1
        v["TSCH_SCHEDULE_CONF_DEFAULT_LENGTH"] = 13
        v["USE_TSCH_WITH_DEDICATED_SLOTS"] = 1
        v["PACKETGEN_PERIOD_MILLISECONDS"] = interval
        generateOptions(OUT_DIRECTORY, "tsch-dedicated-%u"%(interval), v)

        v = copy.copy(variables)
        v["NETSTACK_CONF_RDC_CHANNEL_CHECK_RATE"] = 8
        v["PACKETGEN_PERIOD_MILLISECONDS"] = interval
        generateOptions(OUT_DIRECTORY, "contikmac-%u"%(interval), v)

        v = copy.copy(variables)
        v["USE_NULLRDC"] = 1
        v["PACKETGEN_PERIOD_MILLISECONDS"] = interval
        generateOptions(OUT_DIRECTORY, "nullrdc-%u"%(interval), v)


if __name__ == '__main__':
    main()
    print("all done!")
