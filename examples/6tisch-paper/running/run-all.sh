#!/bin/bash
##########################################

SIMS=../configs
RUNNER=./run-test.py

##########################################

STARTDIR=`pwd`

for d in `ls $SIMS`
do
    cd $SIMS/$d
    $STARTDIR/$RUNNER unused sim.csc $STARTDIR/config.json
    cd $STARTDIR
done

