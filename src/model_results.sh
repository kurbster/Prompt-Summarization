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
    for problem in $(find ../data/*generated/[ic]* -mindepth 1 -type d); do
        ! [[ -f "$problem/report.txt" ]] && report_problem $problem
    done
    for problem in $(find ../data/studio21_generated/ -mindepth 3 -type d); do
        ! [[ -f "$problem/report.txt" ]] && report_problem $problem
    done
}
