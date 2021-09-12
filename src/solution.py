#!/usr/bin/env python3
import os
import sys
import json

if __name__ == '__main__':
    problem, idx = sys.argv[1:]
    fname = os.path.join(problem, 'solutions.json')
    sols = json.load(open(fname))
    idx = int(idx)
    if idx >= len(sols):
        print(sols[-1])
        print(f'The problem {problem} only has {len(sols)} solutions provided.')
        print(f'You asked for the index {idx+1} solution. Printing the last solution available.')
    else:
        print(sols[idx])
