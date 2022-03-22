#!/usr/bin/env bash

levels=(interview competition introductory)

make_dirs() {
    for lvl in "${levels[@]}"; do
        [[ ! -d "$1/$lvl" ]] && mkdir "$1/$lvl"
    done
    find_difficulty $1
}

find_difficulty() {
    for fname in $(find $1/[0-9]* -type d); do
        level=$(awk -F\" '{
            if ($2 == "difficulty") { print $4 }
        }' "$fname/metadata.json")
        mv $fname $1/$level
    done
}

pushd "../../APPS" > /dev/null

make_dirs "train"
make_dirs "test"

popd > /dev/null
