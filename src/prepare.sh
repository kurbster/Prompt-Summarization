#!/bin/bash

pushd ../APPS > /dev/null

[[ ! -d interview ]]    && mkdir interview
[[ ! -d competition ]]  && mkdir competition
[[ ! -d introductory ]] && mkdir introductory

for fname in $(find . -type d -mindepth 2); do
    level=$(sed -e 's/"//g' -e 's/^[ \t]*difficulty: //g' -e 's/[{}]//' "$fname/metadata.json")
    echo "mv $fname "$level""
done

#rm -r 'train test'
popd
