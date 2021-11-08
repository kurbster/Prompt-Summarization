#!/bin/bash

outfile="aggregate_results.csv"
rm "$outfile"

# the output file is formatted like this
# file location, type of summary, word reduction, char reduction
for file in $(find ../data/studio21_generated/*/*/report.txt); do
    echo "$file",$(cat "$file") >> "$outfile"
done

for file in $(find ../data/studio21_generated/*/*/*/report.txt); do
    echo "$file",$(cat "$file") >> "$outfile"
done
