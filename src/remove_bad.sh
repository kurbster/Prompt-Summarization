#!/bin/bash
i=0
for problem in $(find ../data/*generated/[ic]* -mindepth 1 -type d); do
    ! [[ -f "$problem/output.json" ]] && echo $problem && rm -r $problem && i=$((i+1)) || :
done

for problem in $(find ../data/studio21_generated -mindepth 3 -type d); do
    ! [[ -f "$problem/output.json" ]] && echo $problem && rm -r $problem && i=$((i+1)) || :
done

echo $i files removed
