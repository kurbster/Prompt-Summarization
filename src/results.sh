#!/usr/bin/env bash
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
    for problem in $(find ../[ic]* -mindepth 1 -type d); do
        report_problem $problem
    done
} || {
    problem=$(find ../*/$1 -type d)
    [[ -z $problem ]] && echo "$1 is not a valid problem. It has not been summarized." || \
    report_problem $problem
}
