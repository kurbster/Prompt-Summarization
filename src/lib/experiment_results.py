#!/usr/bin/env python3
import os
import sys
import itertools

import pandas as pd

from pathlib import Path

from codex_results import (
    get_accuracy,
    agg_results,
    detect_difficulty,
    detect_summary
)

PATH_TO_DATA = Path(__file__, '../../../data/experiments/aggregate_results').resolve()

def read_pd(fname, **kw):
    df = pd.read_csv(fname, index_col=0, **kw)
    return clean_df(df)

def clean_df(df):
    return df.loc[(df!=0).any(axis=1)]

def get_probs(df, original):
    """Get problems in original that are from df

    Args:
        df (pd.DataFrame): The df with the index values.
        original (pd.DataFrame): The df you want to index.

    Returns:
        pd.DataFrame: The original df, indexed with problems from df.
    """
    summary_type = detect_summary(original.iloc[0].name)
    probs = list(itertools.product(
        df.index,
        ['question.txt', f'{summary_type}.txt']
    ))
    probs = ['/'.join(p) for p in probs]
    return original.loc[probs]

def report_accuracy(df, out_fname: Path, msg: str = ''):
    acc = df.copy(deep=False)
    tot, strict = get_accuracy(acc)
    with open(out_fname, 'a') as f:
        f.write(msg)
        f.write(f'Total Accuracy: {tot:.2f}%\n')
        f.write(f'Strict Accuracy: {strict:.2f}%\n')
    
    print(msg)
    print(f'Total Accuracy: {tot:.2f}%')
    print(f'Strict Accuracy: {strict:.2f}%')

def aggregate_results(df, out_fname, msg: str = ''):
    with open(out_fname, 'a') as out_file:
        summaries = agg_results(df, detect_summary, out_file, msg=msg)
        difficulties = agg_results(df, detect_difficulty, out_file, msg=msg)
    
    print(msg, summaries)
    print(msg, difficulties)

def get_results(df, orig, out_fname: str, msg: str=''):
    new_orig = get_probs(df, orig)
    report_accuracy(new_orig, out_fname, msg='\nAccuracy on ' + msg)
    aggregate_results(new_orig, out_fname, msg='\nAggregate results on ' + msg)

def main(dname: str, out_fname: Path):
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
        names=["Problem Names", -2, -1, False, True])

    # Get the original accuracy
    report_accuracy(orig, out_fname, msg='Entire experiment accuracy:\n')

    get_results(better, orig, out_fname,
        msg='problems that got better:\n')

    get_results(same, orig, out_fname,
        msg='problems that stayed the same:\n')
    
    same_or_better = pd.merge(same, better, how='outer', left_index=True, right_index=True)
    get_results(same_or_better, orig, out_fname,
        msg='problems that got better or stayed the same:\n')


if __name__ == '__main__':
    dname = sys.argv[1]
    out_dir = PATH_TO_DATA.joinpath('new-results', dname)
    out_fname = out_dir.joinpath('results.txt')
    if out_fname.exists():
        print('This experiment has already been recalculated.')
        print('Remove the results.txt file then rerun the script.')
        sys.exit(1)
        
    out_dir.mkdir(parents=True, exist_ok=True)
    main(dname, out_fname)