#!/usr/bin/env bash

get_generated_human() {
    [[ ! -z $1 ]] && dname="-name $1"
    problems=$(find ../../data/human_generated/*/[ic]* -mindepth 1 -type d $dname)
}

get_generated_model() {
    [[ -z $1 ]] && api="*" || api="$1"
    problems=$(find ../../data/$api"_generated"/*/[ic]* -mindepth 1 \
        -not -path *human* -type d)
}

# If this script was run directly
[[ ${#BASH_SOURCE[@]} == 1 ]] && {
    get_generated_model
    echo "$(wc -l <<< $problems) model problems generated."
    get_generated_model "studio21"
    echo "$(wc -l <<< $problems) studio 21 model problems generated."
    get_generated_model "gpt"
    echo "$(wc -l <<< $problems) gpt model problems generated."
    get_generated_human
    echo "$(wc -l <<< $problems) human problems generated."
    echo -e "$problems\n" | awk -F"data/" '{print $2}' > ../configs/human_probs.txt
    sed -E -i '/^[[:space:]]*$/d' ../configs/human_probs.txt
}
