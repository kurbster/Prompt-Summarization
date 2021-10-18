#!/usr/bin/env bash
files=(question.txt summary.txt expert.txt)
num="$1"

report_problem() {
    pushd $1 > /dev/null
    echo -e "\nwc results for problem $1"
    echo "   lines   words   chars"
    result=$(wc -lwm ${files[@]})
    echo "$result"
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
    }' <<< $result
    popd > /dev/null
}

[[ -z $num ]] && echo "report all problems" && {
    for problem in $(find .. -mindepth 2 -type d -not -path "../.git*" -not -path "../APPS/*"); do
        report_problem $problem
    done
} || {
    problem=$(find ../*/$num -type d)
    report_problem $problem
}
