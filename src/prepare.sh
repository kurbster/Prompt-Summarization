#!/bin/bash

pushd "../apps_dataset/APPS" > /dev/null

levels=(interview competition introductory)
for lvl in "${levels[@]}"; do
    [[ ! -d $lvl ]] && mkdir $lvl
done

for fname in $(find 'train' -mindepth 1 -type d); do
    level=$(awk -F[:,\"] '{print $5}' "$fname/metadata.json")
    mv $fname $level
done

rm -r train 'test' README.txt

# we are in apps_dataset/APPS
cd ../..
mv apps_dataset/APPS .
rmdir apps_dataset

popd > /dev/null
