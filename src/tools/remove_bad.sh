#!/usr/bin/env bash

. find_files.sh

i=0

get_generated_model
for problem in $problems; do
    ! [[ -f "$problem/output.json" ]] && echo $problem && rm -r $problem && i=$((i+1)) || :
done

echo $i files removed
