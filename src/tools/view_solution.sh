#!/usr/bin/env bash

. find_files.sh

num="${1:? You must pass a problem number to print a solution for.}"
idx="${2:-0}"

get_generated_human $num
problem=$problems

[[ -z $problem ]] && echo "$num is not a valid problem" || python3 solution.py $problem $idx
