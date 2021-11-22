#!/bin/bash

filter="${1:-100}"

# To filter by word reduction this should be 3
# To filter by char redution this should be 4
column=3

awk -F, -v col=$column -v lim=$filter 'NR>=2 {
if ($col >= lim) {
    print $1
}
}' aggregate_results.csv | \
    xargs dirname
