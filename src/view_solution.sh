#!/bin/bash

num="${1:? You must pass a problem number to print a solution for.}"
idx="${2:-0}"

problem=$(find ../data/[ic]*/$num -type d)

[[ -z $problem ]] && echo "$num is not a valid problem" || python3 solution.py $problem $idx
