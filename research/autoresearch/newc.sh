#!/bin/zsh
# usage: ./newc.sh id parent "hypothesis" "change" "expect" 'ALT list' 'feature expression' 'fit_predict expression'
cd "$(dirname "$0")"
cat > candidates/$1.py <<PY
import numpy as np
import lib
ID, PARENT = "$1", "$2"
HYP = "$3"
CHANGE = "$4"
EXPECT = "$5"
ALT, D_BAND, SMOOTH, SEEDS = $6, 0.0, 1, 1


def features(D):
    return $7


fit_predict = $8
PY
