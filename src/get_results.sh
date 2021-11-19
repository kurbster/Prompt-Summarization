#!/bin/bash

outfile="aggregate_results.csv"
rm "$outfile"

# the output file is formatted like this
# file location, type of summary, word reduction, char reduction
for file in $(find ../data/*generated/[ic]*/*/report.txt); do
    echo "$file",$(cat "$file") >> "$outfile"
done

# Get the results from the test dir
for file in $(find ../data/*generated/*/*/*/report.txt); do
    echo "$file",$(cat "$file") >> "$outfile"
done
