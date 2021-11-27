#!/usr/bin/env bash

. find_files.sh

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

get_generated_model
for problem in $problems; do
    ! [[ -f "$problem/report.txt" ]] && report_problem $problem
done
