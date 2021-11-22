#!/bin/bash

levels=(interview competition introductory)

make_dirs() {
    for lvl in "${levels[@]}"; do
        [[ ! -d $lvl ]] && mkdir $lvl
    done
}

find_difficulty() {
    for fname in $(find $1 -not -path train -type d); do
        trimmed=$(tr '\n' ' ' < "$fname/metadata.json")
        level=$(awk -F\" '{
            if ($2 == "url") { print $8 }
            else if ($2 == "difficulty") { print $4 }
            else { print ERROR }
        }' <<< $trimmed)
        mv $fname $level
    done
}

pushd "../../apps_dataset/APPS" > /dev/null

make_dirs && find_difficulty "train"

pushd "test" > /dev/null

make_dirs && find_difficulty "[0-9]*"

popd > /dev/null

rm -r train README.txt

# we are in apps_dataset/APPS
cd ../..
mv apps_dataset/APPS .
rmdir apps_dataset

popd > /dev/null
