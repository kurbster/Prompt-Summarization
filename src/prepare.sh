#!/bin/bash

levels=(interview competition introductory)

make_dirs() {
    for lvl in "${levels[@]}"; do
        [[ ! -d $lvl ]] && mkdir $lvl
    done
}

find_difficulty() {
    for fname in $(find $1 -mindepth 1 -type d); do
        level=$(awk -F[:,\"] '{print $5}' "$fname/metadata.json")
        mv $fname $level
    done
}

pushd "../apps_dataset/APPS" > /dev/null

make_dirs && find_difficulty 'train'

pushd 'test' > /dev/null

make_dirs && find_difficulty '.'

popd > /dev/null

rm -r train README.txt

# we are in apps_dataset/APPS
cd ../..
mv apps_dataset/APPS .
rmdir apps_dataset

popd > /dev/null
