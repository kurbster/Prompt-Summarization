#!/usr/bin/env python3
import sys
import json
import glob

out = sys.argv[1]
summary_type = sys.argv[2]

human_probs = glob.glob('../../data/[ic]*/*')
print(len(human_probs))

probs = []

for prob in human_probs:
    with open(f'{prob}/question.txt') as f:
        orig = f.read()
    with open(f'{prob}/{summary_type}.txt') as f:
        summary = f.read()

    output = {'prompt': orig, 'completion': summary}
    probs.append(output)

with open(out, 'w') as f:
    json.dump(probs, f, indent=4)
