#!/bin/bash

pushd ../APPS > /dev/null

[[ ! -d interview ]]    && mkdir interview
[[ ! -d competition ]]  && mkdir competition
[[ ! -d introductory ]] && mkdir introductory

for fname in $(find 'train' -mindepth 1 -type d); do
    level=$(sed -e 's/"//g' -e 's/^[ \t]*difficulty: //g' -e 's/[{}]//' "$fname/metadata.json")
    mv $fname $level
done

rm -r train 'test' README.txt

popd > /dev/null
