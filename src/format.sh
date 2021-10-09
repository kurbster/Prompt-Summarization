#!/bin/bash

files=(question.txt summary.txt expert.txt)

clean_problem() {
    # $1 - the problem directory
    # $2 - the filename to clean
    ! [[ -f $1/$2 ]]  && echo "ERROR. You must add the file $2 to this directory $1." && error=1 || {
        trim=$(sed -E -e 's/-{5}Input-{5}/Input:/' -e 's/-{5}Output-{5}/Output:/' -e 's/-{5}Examples-{5}/Examples:/' -e 's/-{5}Note-{5}/Note:/' "$1/$2")
        tr -d "[\t\n\r]" <<< $trim > "$1/clean-$2"
    }
}

for problem in $(find .. -mindepth 2 -type d -not -path "../.git*" -not -path "../APPS/*"); do
    for file in "${files[@]}"; do
        ! [[ -f $problem/clean-$file ]] \
            && echo "Problem $problem/$file needs to be cleaned." \
            && clean_problem $problem $file
    done
done

[[ ! -z $error ]] && echo "Fix the error then run the format.sh script again" || echo "All problems cleaned."
