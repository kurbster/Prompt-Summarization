#!/usr/bin/env bash

get_generated_train() {
    problems=$(find ../../data/*generated/[ic]* -mindepth 1 -type d)
}

get_generated_test() {
    problems=$(find ../../data/*generated/ -mindepth 3 -type d)
}

get_generated_human() {
    [[ -z $1 ]] && problems=$(find ../../data/[ic]* -mindepth 1 -type d) ||\
    problems=$(find ../../data/[ic]*/$1 -type d)
}

get_generated_model() {
    problems=$(find ../../data/*generated/[ic]* -mindepth 1 -type d && \
             find ../../data/*generated/ -mindepth 3 -type d)
}

# If this script was run directly
[[ ${#BASH_SOURCE[@]} == 1 ]] && {
    get_generated_train
    echo "$(wc -l <<< $problems) train problems generated."
    get_generated_test
    echo "$(wc -l <<< $problems) test problems generated."
    get_generated_model
    echo "$(wc -l <<< $problems) model problems generated."
    get_generated_human
    echo "$(wc -l <<< $problems) human problems generated."
    echo -e "$problems\n" | awk -F"data/" '{print $2}' > ../configs/human_probs.txt
    sed -i '/^[[:space:]]*$/d' ../configs/human_probs.txt
}
