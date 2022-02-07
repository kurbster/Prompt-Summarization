#!/usr/bin/env python3
import sys
import json
import itertools

import numpy as np
import pandas as pd

from typing import Iterable, Tuple, Callable
from pathlib import Path

from experiment_results import get_probs, read_pd
from codex_results import get_accuracy, detect_summary

PATH_TO_DATA = Path(__file__, '../../../data/experiments/aggregate_results').resolve()
PATH_TO_HUMAN_DATA = Path(__file__, '../../../data/human_generated/train').resolve()
PATH_TO_GPT_DATA = Path(__file__, '../../../data/').resolve()

RESULT_TYPES = {
    'original': 'question.txt',
    'summary': 'summary.txt',
    'expert': 'expert.txt',
    'solution': 'solutions.json',
    'generated': 'all_codes.json'
}

# There's probably a more clever way to combine these functions
def get_text_len(problems: Iterable, result_type: str):
    lengths = []
    ftype = RESULT_TYPES[result_type]
    for prob in problems:
        fname = PATH_TO_HUMAN_DATA.joinpath(prob, ftype)
        with open(fname) as f:
            text = f.read()
        lengths.append(len(text))
    return lengths

def get_json_len(problems: Iterable, result_type: str, agg_func: Callable):
    lengths = []
    ftype = RESULT_TYPES[result_type]
    for prob in problems:
        fname = PATH_TO_HUMAN_DATA.joinpath(prob, ftype)
        if not fname.exists():
            lengths.append(0)
            continue
        with open(fname) as f:
            sols = json.load(f)
        lens = list(map(len, sols))
        arr = np.array(lens)
        lengths.append(agg_func(arr))
    return lengths

def get_code_len(problems: Iterable, result_type: str, result_dir: str) -> Tuple[np.array, np.array]:
    original_lengths, summary_lengths = [], []
    ftype = RESULT_TYPES[result_type]
    fname = PATH_TO_DATA.joinpath(result_dir, ftype)

    with open(fname) as f:
        codes = json.load(f)
    code_len = list(map(len, codes))
    problem_types = list(map(lambda x: detect_summary(x), problems))

    for length, prob in zip(code_len, problem_types):
        if prob == 'question':
            original_lengths.append(length)
        else:
            summary_lengths.append(length)

    return np.array(original_lengths), np.array(summary_lengths)

def get_problem_accuracy(problems: Iterable, accuracy: pd.Series, result_type: str):
    accuracies = []
    ftype = RESULT_TYPES[result_type]
    for prob in problems:
        query = f'{prob}/{ftype}'
        accuracies.append(accuracy.loc[query])
    
    return np.array(accuracies)

def find_summary_used(df: pd.DataFrame) -> str:
    """This will return a string representing the type of
    summary used in this experiment, which is represented by the df.

    Args:
        df (pd.DataFrame): The dataframe containing the raw results
        of the experiment.

    Returns:
        str: A string of the summary type used. (summary or expert)
    """
    problems = df.iloc[:2]
    for prob in problems.index:
        prob_type = detect_summary(prob)
        # If the problem was not the original then we return
        if prob_type != 'question':
            return prob_type

def compute_statistics(df: pd.DataFrame, accuracy: pd.Series, result_dir: str):
    problems = df.index
    results = pd.DataFrame(index=problems,
        columns=[
            'Original Len',
            'Summary Len',
            'Summarization Percent',
            'Code Solution Min Len',
            'Code Solution Mean Len',
            'Original Code Generated Len',
            'Summary Code Generated Len',
            'Test Cases',
            'Original Accuracy',
            'Summary Accuracy',
            'Accuracy Increase'
        ]
    )

    summary_type = find_summary_used(accuracy)
    results['Original Len'] = get_text_len(problems, 'original')
    results['Summary Len']  = get_text_len(problems, summary_type)
    results['Summarization Percent'] = 100 * (results['Original Len'] - results['Summary Len']) / results['Original Len']
    
    results['Code Solution Min Len']  = get_json_len(problems, 'solution', np.min)
    results['Code Solution Mean Len'] = get_json_len(problems, 'solution', np.mean)

    orig_code_len, summary_code_len = get_code_len(accuracy.index, 'generated', result_dir)
    results['Original Code Generated Len'] = orig_code_len
    results['Summary Code Generated Len']  = summary_code_len

    results['Test Cases'] = df.sum(axis=1)
    results['Original Accuracy'] = get_problem_accuracy(problems, accuracy, 'original')
    results['Summary Accuracy']  = get_problem_accuracy(problems, accuracy, summary_type)
    results['Accuracy Increase'] = results['Summary Accuracy'] - results['Original Accuracy']

    return results

def main(dname: str, is_gpt=False):
    # Need to set the proper parent path if we are looking @ GPT results.
    if is_gpt:
        global PATH_TO_HUMAN_DATA
        PATH_TO_HUMAN_DATA = PATH_TO_GPT_DATA
        print('I was ran.')

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

    results = compute_statistics(same_or_better, orig_same_or_better.acc, dname)
    outfile = dirname.joinpath('results.csv')
    results.to_csv(outfile)

    return results

if __name__ == '__main__':
    dname = sys.argv[1]
    is_gpt = False
    if len(sys.argv) == 3:
        is_gpt = bool(sys.argv[2])
    results = main(dname, is_gpt=is_gpt)