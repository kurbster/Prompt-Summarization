#!/usr/bin/env bash

. find_files.sh

outfile="aggregate_results.csv"
rm "$outfile"

# the output file is formatted like this
# file location, type of summary, word reduction, char reduction
get_generated_model
for file in $problems; do
    fname=${file#*"data/"}
    echo "${fname}/report.txt",$(cat "$file/report.txt") >> "$outfile"
done
