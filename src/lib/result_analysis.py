#!/usr/bin/env python3
import sys
import itertools

import numpy as np
import pandas as pd

from pathlib import Path

from experiment_results import get_probs, read_pd
from codex_results import get_accuracy, detect_summary

PATH_TO_DATA = Path(__file__, '../../../data/experiments/aggregate_results').resolve()
PATH_TO_HUMAN_DATA = Path(__file__, '../../../data/human_generated/train').resolve()

RESULT_TYPES = {
    'original': 'question.txt',
    'summary': 'summary.txt',
    'expert': 'expert.txt',
}
def get_len(problems, result_type):
    try:
        ftype = RESULT_TYPES[result_type]
    except KeyError as e:
        print(f'You asked for type {result_type}. Can only specify {RESULT_TYPES.keys()}.')
        raise KeyError(str(e))

    lengths = []
    for prob in problems:
        fname = PATH_TO_HUMAN_DATA.joinpath(prob, ftype)
        with open(fname) as f:
            text = f.read()
        lengths.append(len(text))
    
    return np.array(lengths)

def find_summary_used(df):
    problems = df.iloc[:2]
    for prob in problems.index:
        prob_type = detect_summary(prob)
        # If the problem was not the original then we return
        if prob_type != 'question':
            return prob_type

def compute_statistics(df, accuracy):
    problems = df.index
    results = pd.DataFrame(index=problems,
        columns=[
            'Original Len',
            'Summary Len',
            'Summarization Percent',
            'Code Solution Len',
            'Original Code Generated Len',
            'Summary Code Generated Len',
            'Test Cases',
            'Original Accuracy',
            'Summarized Accuracy'
        ]
    )
    summary_type = find_summary_used(accuracy)
    results['Original Len'] = get_len(problems, 'original')
    results['Summary Len']  = get_len(problems, summary_type)
    results['Summarization Percent'] = 100 * (results['Original Len'] - results['Summary Len']) / results['Original Len']
    
    return results

def main(dname: str):
    dirname = PATH_TO_DATA.joinpath(dname)
    fname = dirname.joinpath('better_df.csv')
    better = read_pd(fname)

    fname = dirname.joinpath('same_df.csv')
    same = read_pd(fname)

    fname = dirname.joinpath('original_df.csv')
    orig = read_pd(
        fname, 
        usecols=[0, 1, 2, 3, 4],
        header=0,
        names=["Problem Names", -2, -1, False, True]
    )
    same_or_better = pd.merge(same, better, how='outer', left_index=True, right_index=True)

    orig_same_or_better = get_probs(same_or_better, orig)
    total, strict = get_accuracy(orig_same_or_better)
    print(f'Total Accuracy: {total:.2f}%')
    print(f'Strict Accuracy: {strict:.2f}%')

    return compute_statistics(same_or_better, orig_same_or_better.acc)

if __name__ == '__main__':
    dname = sys.argv[1]
    results = main(dname)