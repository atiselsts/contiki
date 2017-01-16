#!/usr/bin/env python3

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
# Author: Atis Elsts, 2017
#

import os, sys, time, threading, re, signal
from subprocess import Popen, PIPE, STDOUT
import socket

def runSubprocess(args, env = None):
    index = args[-1]
    args = " ".join(args[:-1])
    # sys.stdout.write("Run subprocess: " + args + "\n")
    retcode = -1
    f = open("node" + str(index) + ".txt", "wb")
    try:
        proc = Popen(args, stdout = PIPE, stderr = STDOUT, shell = True, env = env)
        while proc.poll() is None:
            # Be careful not to cause a deadlock: read by small portions until each newline.
            # Warning! If the child process can produce a lot of data without newlines,
            # the Python code must be modified to use limited-sized read(N) instead of readline()!
            data = proc.stdout.readline()
            if data:
                sys.stdout.buffer.write(data)
                sys.stdout.flush()
                f.write(data)
                f.flush()
            time.sleep(0.001)
        data = proc.stdout.read()
        if data:
            sys.stdout.buffer.write(data)
            sys.stdout.flush()
            f.write(data)
            f.flush()
        retcode = proc.returncode
    except OSError as e:
        print("run subprocess OSError:" + str(e))
    except CalledProcessError as e:
        print("run subprocess CalledProcessError:" + str(e))
        retcode = e.returncode
    except Exception as e:
        print("run subprocess exception:" + str(e))
    finally:
        print("done, retcode = " + str(retcode))
        f.close()
        return retcode


def createThread(function, args):
    # make sure 'args' is a list or a tuple
    if not (type(args) is list or type(args) is tuple):
        args = (args,)
    t = threading.Thread(target=function, args=args)
    t.start() 


def runLogger(index):
    SD="../../../tools/sky/serialdump-linux"
    args = [SD, "/dev/ttyUSB" + str(index), index]
    runSubprocess(args)

SD="../../../tools/sky/serialdump-linux"
for i in range(5):
    createThread(runLogger, i)

#signal.signal(signal.SIGINT, cleanup)
#signal.signal(signal.SIGTERM, cleanup)
while True:
    time.sleep(1)
