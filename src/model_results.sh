#!/bin/bash
files=(question.txt expert.txt)
outfile="report.txt"

report_problem() {
    pushd $1 > /dev/null

    result=$(wc -lwm ${files[@]})
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
            printf "%s,%.2f,%.2f\n", $NF, outW, outC
        }
    }' <<< "$result" > "$outfile"

    popd > /dev/null
}

[[ -z $1 ]] && echo "report all problems" && {
    for problem in $(find ../model_generated/* -mindepth 1 -type d); do
        report_problem $problem
    done
} || {
    problem=$(find ../model_generated/*/$1 -type d)
    [[ -z $problem ]] && echo "$1 is not a valid problem. It has not been summarized." || \
    report_problem $problem
}
