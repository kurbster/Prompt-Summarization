#!/usr/bin/env bash

get_generated_human() {
    [[ ! -z $1 ]] && dname="-name $1"
    problems=$(find ../../data/human_generated/*/[ic]* -mindepth 1 -type d $dname)
}

get_generated_model() {
    [[ -z $1 ]] && api="*" || api="$1"
    problems=$(find ../../data/$api"_generated"/*/* -mindepth 1 -type d -not -path '*ARCHIVE*' \
    -and -not -path '*human*')
}

# If this script was run directly
[[ ${#BASH_SOURCE[@]} == 1 ]] && {
    get_generated_model
    echo "$(wc -l <<< ${problems}) model problems generated."

    # Was unable to make the awk and sed commands a function
    # When passing the args echo and awk did not iterate as expected
    get_generated_model "studio21"
    echo "$(wc -l <<< ${problems}) studio 21 model problems generated."
    echo -e "${problems}\n" | awk -F"data/" '{print $2}' > ../configs/manifests/all_studio_generated.txt
    sed -E -i '/^[[:space:]]*$/d' ../configs/manifests/human_probs.txt

    get_generated_model "gpt"
    echo "$(wc -l <<< ${problems}) gpt model problems generated."
    echo -e "${problems}\n" | awk -F"data/" '{print $2}' > ../configs/manifests/gpt_generated.txt
    sed -E -i '/^[[:space:]]*$/d' ../configs/manifests/human_probs.txt

    get_generated_human
    echo "$(wc -l <<< ${problems}) human problems generated."
    echo -e "${problems}\n" | awk -F"data/" '{print $2}' > ../configs/manifests/human_probs.txt
    sed -E -i '/^[[:space:]]*$/d' ../configs/manifests/human_probs.txt
}
