#!/usr/bin/env python3
import json
import argparse

import numpy as np
import pandas as pd

from typing import Iterable, Tuple, Callable
from pathlib import Path

from experiment_results import get_orig_better_worse_same, get_probs
from codex_results import get_accuracy, detect_summary, split_prob

PATH_TO_EXP = Path(__file__, '../../../data/experiments').resolve()
PATH_TO_DATA = Path(__file__, '../../../data/').resolve()

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
        fname = PATH_TO_DATA.joinpath(prob, ftype)
        with open(fname) as f:
            text = f.read()
        lengths.append(len(text))
    return lengths

def get_json_len(problems: Iterable, result_type: str, agg_func: Callable):
    lengths = []
    ftype = RESULT_TYPES[result_type]
    for prob in problems:
        fname = PATH_TO_DATA.joinpath(prob, ftype)
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
    code_fname = PATH_TO_EXP.joinpath(result_dir, ftype)
    index_fname = PATH_TO_EXP.joinpath(result_dir, 'test.json')

    with open(code_fname) as f:
        codes = json.load(f)
    with open(index_fname) as f:
        index = json.load(f)

    code_len = list(map(len, codes.values()))

    index = list(map(split_prob, index))
    # Create df with all problems
    code_df = pd.DataFrame(code_len, index=index, columns=['Code Len'])
    # Get specific problems we are looking at
    code_df = code_df.loc[problems]

    # Check to see if summary or question come first
    if detect_summary(code_df.index[0]) == 'question':
        original_lengths = code_df.iloc[0::2]
        summary_lengths = code_df.iloc[1::2]
    else:
        original_lengths = code_df.iloc[1::2]
        summary_lengths = code_df.iloc[0::2]

    return original_lengths.values, summary_lengths.values

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

def change_from_agave(*args):
    outputs = []
    for df in args:
        df.index = df.index.map(lambda x: x.replace('/scratch/kkuznia', '/media/HD/Documents/Prompt-Summarization/data'))
        outputs.append(df)
    return outputs

def main(dname: str, ftype: str="", get_all_results=False):
    dirname = PATH_TO_EXP.joinpath(dname)
    orig, better, worse, same = get_orig_better_worse_same(dirname, ftype)
    orig, better, worse, same = change_from_agave(orig, better, worse, same)

    same_or_better = pd.merge(same, better, how='outer', left_index=True, right_index=True)
    if get_all_results:
        same_or_better = pd.merge(worse, same_or_better, how='outer', left_index=True, right_index=True)

    orig_same_or_better = get_probs(same_or_better, orig, summary_type=ftype)
    total, strict = get_accuracy(orig_same_or_better)
    print(f'Total Accuracy: {total:.2f}%')
    print(f'Strict Accuracy: {strict:.2f}%')

    results = compute_statistics(same_or_better, orig_same_or_better.acc, dname)
    results.index = results.index.map(lambda x: x.split('data/')[-1])
    outfile = dirname.joinpath(f'{ftype}_results.csv')
    results.to_csv(outfile)

    return results

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-o', '--output_dir', type=Path, required=True)
    parser.add_argument('-l', '--file_list', nargs='+', required=True)
    args = parser.parse_args()
    print(args)

    for ftype in args.file_list:
        results = main(args.output_dir, ftype=ftype, get_all_results=True)