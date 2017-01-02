#!/usr/bin/python3

# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#  * Redistributions of source code must retain the above copyright notice,
#    this list of  conditions and the following disclaimer.
#  * Redistributions in binary form must reproduce the above copyright
#   notice, this list of conditions and the following disclaimer in the
#   documentation and/or other materials provided with the distribution.
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS OR
# CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS;
# OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
# WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR
# OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF
# ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

#
# Test control file.
#
# This should be run as root, because it needs a user with CAP_NET_ADMIN capability.
#
# Author: Atis Elsts, 2016
#

import os, sys, copy, time, signal, errno
import tests

##########################################

CONTIKI_PATH   = "/home/atis/work/contiki-git"

COOJA = "java -jar " + CONTIKI_PATH + "/tools/cooja/dist/cooja.jar -nogui="

COOJA_LOG_FILE = "COOJA.testlog"

# TODO: should get rid of these two
MSP430_PATH =  "/usr/local/msp430/bin"
JAVA_HOME = "/usr/lib/jvm/java-8-openjdk-amd64"

##########################################

class Process:
    def __init__(self, args):
        self.args = copy.copy(args)
        self.pid = None

    def run(self):
        #print("run...")
        #print("args=", self.args)

        try:
            self.pid = os.fork()
        except OSError as e:
            print("run failed: ", e.strerror)
            raise Exception("%s [%d]" % (e.strerror, e.errno))

        if self.pid == 0:
            # child; run the program in the args list
            os.execvp(self.args[0], self.args)
            print("execvp failed! args=", args)
            exit(-1)

        #print("started child: ", self.pid)

        # add to running processes
        runningProcesses[self.pid] = self

    def kill(self):
        if self.pid is None or self.pid == 0:
            return
        try:
            os.kill(self.pid, signal.SIGKILL)
        except Exception as ex:
            print('killing process with PID {} failed: '.format(self.pid, ex))
        else:
            del runningProcesses[self.pid]
            self.pid = None

runningProcesses = {}

##########################################

def signalHandler(sig, frame):
    if sig == signal.SIGCHLD:
        pid, code = os.wait()
        if pid not in runningProcesses:
            print("Unknown child exited, pid: ", pid)
        else:
            # set pid of the process to None to signal that it doesn't have to be killed
            runningProcesses[pid].pid = None
            # remove it form the map as well
            del runningProcesses[pid]

##########################################
def waitForTermination(cooja):
    # while the children have not exited...
    while cooja.pid in runningProcesses:
        time.sleep(5)
    return 0

##########################################
def silentremove(filename):
    try:
        os.remove(filename)
    except OSError as e:
        if e.errno != errno.ENOENT:
            # re-raise; may be permission error or so
            raise

##########################################

def isReadable(filename):
    return os.path.isfile(filename) and os.access(filename, os.R_OK)

##########################################
def main():
    if len(sys.argv) < 3:
        print("not enough args: ", sys.argv)
        return -1

    # update the environmental variables if needed
    os.environ["JAVA_HOME"] = os.environ.get("JAVA_HOME", JAVA_HOME)
    os.environ["PATH"] = MSP430_PATH + ":" + os.environ.get("PATH", "")

    # check the cooja file
    coojaFile = sys.argv[2]
    if not isReadable(coojaFile):
        print("coojaFile not readable")
        return -1

    # execute cooja
    coojaCmdline = COOJA + coojaFile
    args = coojaCmdline.split()
    cooja = Process(args)

    # install handler to notify us when a child has quit
    signal.signal(signal.SIGCHLD, signalHandler)

    # remove old log files, is existing
    try:
        silentremove(COOJA_LOG_FILE)
    except Exception as ex:
        print('Failed to remove old log files: '.format(ex))
        return -1

    try:
        cooja.run()
    except Exception as ex:
        print('Failed to run Cooja: '.format(ex))
        return -1

    ret = waitForTermination(cooja)

    cooja.kill()

    return ret

###########################################

if __name__ == '__main__':
    exit(main())
