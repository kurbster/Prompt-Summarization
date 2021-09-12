#!/bin/bash

files=(question.txt summary.txt instruction.txt expert.txt)

clean_problem() {
    for file in "${files[@]}"; do
        ! [[ -f $1/$file ]] && echo "ERROR. You must add the file $file to this directory $1." && error=1 || {
            trim=$(sed -E -e 's/-{5}Input-{5}/Input:/' -e 's/-{5}Output-{5}/Output:/' -e 's/-{5}Examples-{5}/Examples:/' -e 's/-{5}Note-{5}/Note:/' "$1/$file")
            tr -d "[\t\n\r]" <<< $trim > "$1/clean-$file"
        }
    done
}

for problem in $(find .. -type d -not -path "../.git*" -mindepth 2); do
    for file in "${files[@]}"; do
        ! [[ -f $problem/clean-$file ]] \
            && echo "Problem $problem needs to be cleaned." \
            && clean_problem $problem
    done
done

[[ ! -z $error ]] && echo "Fix the error then run the format.sh script again" || echo "All problems cleaned."
