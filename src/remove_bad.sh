#!/bin/bash
i=0
for problem in $(find "../model_generated" -mindepth 2 -type d); do
    ! [[ -f "$problem/output.json" ]] && echo $problem && rm -r $problem && i=$((i+1)) || :
done

echo $i files removed
