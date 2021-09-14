#!/bin/bash

wget 'https://people.eecs.berkeley.edu/~hendrycks/APPS.tar.gz'

echo "Extracting dataset to parent directory ..."
tar -xzf 'APPS.tar.gz' -C ..
echo "Done. Now separating the problems according to difficulty"

rm APPS.tar.gz

bash prepare.sh
