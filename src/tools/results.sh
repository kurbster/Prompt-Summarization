#!/usr/bin/env bash

. find_files.sh

files=(question.txt summary.txt expert.txt)
outfile="report.txt"

report_problem() {
    pushd $1 > /dev/null
    echo -e "\nwc results for problem $1"
    echo "line word char" | tee "$outfile"
    result=$(wc -lwm ${files[@]})
    echo "$result" | tee -a "$outfile"
    printf "\nWord reduction percentage\n%-11s %-6s %-6s\n" filename words chars
    awk '{
        if ($NF == "question.txt")
        {
            word=$2
            char=$3
        }
        else if ($NF == "total") {}
        else
        {
            diffW=word-$2
            diffC=char-$3
            outW=(diffW/word)*100
            outC=(diffC/char)*100
            printf "%-11s %.2f%% %.2f%%\n", $NF, outW, outC
        }
    }' <<< $result | tee -a "$outfile"
    popd > /dev/null
}

[[ -z $1 ]] && echo "report all problems" && {
    get_generated_human
    for problem in $problems; do
        report_problem $problem
    done
} || {
    get_generated_human $1
    problem=$problems
    [[ -z $problem ]] && echo "$1 is not a valid problem. It has not been summarized." || \
    report_problem $problem
}
