#!/usr/bin/env python3
import re
import os
import glob

files = glob.glob('../[ic]*/*/question.txt')
other = glob.glob('../model_generated/*/*/question.txt')
files = files + other

with open('split.txt') as f:
    re_str = f.read().splitlines()

re_str = '|'.join(re_str)
regex = re.compile(re_str)

def split_question(fname: str) -> str:
    # Read the prompt
    prompt = []
    with open(fname) as f:
        prompt = f.readlines()
    
    # Strip newlines
    prompt = [p.strip('\n') for p in prompt if p != '\n']
    prompt = ' '.join(prompt)

    prompt_split = False
    match = regex.search(prompt)
    if match:
        prompt_idx = match.span()[0]
        prompt_split = True
    else:
        name = os.path.split(fname)[0]
        print(f'For file {name} We did not find a split!!!')

    return prompt_split

num_splits = 0
for p in files:
    if split_question(p):
        num_splits += 1
print(f'We found a split for {num_splits} files. Out of {len(files)} total. Splitting {100*num_splits/len(files):.2f}%')
