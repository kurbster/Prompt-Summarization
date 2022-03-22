#!/usr/bin/env python3
import sys
import itertools
import argparse

import pandas as pd

from typing import List, Tuple
from pathlib import Path

try:
    from codex_results import (
        get_accuracy,
        agg_results,
        detect_difficulty,
        detect_summary,
        write_df
    )
except ModuleNotFoundError:
    from .codex_results import (
        get_accuracy,
        agg_results,
        detect_difficulty,
        detect_summary,
        write_df
    )


PATH_TO_DATA = Path(__file__, '../../../data/experiments/aggregate_results').resolve()

def read_pd(fname, **kw):
    return pd.read_csv(fname, index_col=0, **kw) 

def get_probs(df, original, summary_type: str):
    """Get problems in original that are from df

    Args:
        df (pd.DataFrame): The df with the index values.
        original (pd.DataFrame): The df you want to index.
        summary_type (str): The type of the summary wanted.

    Returns:
        pd.DataFrame: The original df, indexed with problems from df.
    """
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

def aggregate_results(df, out_fname, msg: str = '', new_file: Path=None):
    with open(out_fname, 'a') as out_file:
        summaries = agg_results(df, detect_summary, out_file, msg=msg, new_file=new_file)
        difficulties = agg_results(df, detect_difficulty, out_file, msg=msg, new_file=new_file)
    
    print(msg, summaries)
    print(msg, difficulties)

def get_score_of_columns(df: pd.DataFrame) -> List[int]:
    scores_dict = {'-2': -2, '-1': -1, 'False': 0, 'True': 1}
    scores = []
    for col in df.columns:
        first_val, second_val = col.split('=>')
        first_score = scores_dict[first_val]
        second_score = scores_dict[second_val]
        scores.append(second_score - first_score)
    
    return scores

def get_compare_score(df: pd.DataFrame, out_fname: str, msg: str=""):
    scores = get_score_of_columns(df)
    score_df = df.sum().mul(scores)
    score_df.name = 'score'

    total_score = score_df.sum()
    with open(out_fname, 'a') as out_file:
        write_df(
            score_df,
            out_file,
            idx_label='From=>To',
            msg=msg
        )
        out_file.write(f'Total score difference: {total_score}\n')

def get_results(df, orig, out_fname: str, summary_type: str, msg: str='', get_orig: bool=True, new_file: Path=None):
    if get_orig:
        orig = get_probs(df, orig, summary_type)
    if len(orig) > 0:
        report_accuracy(orig, out_fname, msg=f'\n{summary_type} Accuracy on ' + msg)
        aggregate_results(orig, out_fname, msg=f'\n{summary_type} Aggregate results on ' + msg, new_file=new_file)

def get_orig_better_worse_same(dirname: Path, ftype: str) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    fname = dirname.joinpath(f'{ftype}_better_df.csv')
    better = read_pd(fname)

    fname = dirname.joinpath(f'{ftype}_same_df.csv')
    same = read_pd(fname)

    fname = dirname.joinpath(f'{ftype}_worse_df.csv')
    worse = read_pd(fname)

    fname = dirname.joinpath(f'original_df.csv')
    orig = read_pd(
        fname, 
        usecols=[0, 1, 2, 3, 4],
        header=0,
        names=["Problem Names", -2, -1, False, True]
    )

    return orig, better, worse, same

def remove_probs(probs_to_remove: pd.Index, df: pd.DataFrame, ftypes=None):
    def add_fname(x, fname):
        return f'{x}/{fname}'

    if ftypes:
        original_probs = probs_to_remove.map(lambda x: add_fname(x, 'question.txt'))
        for ftype in ftypes:
            new_probs = probs_to_remove.map(lambda x: add_fname(x, f'{ftype}.txt'))
            original_probs = original_probs.union(new_probs)
        probs_to_remove = original_probs
    
    return df.drop(probs_to_remove)

def main(dirname: Path, out_fname: str, file_types: List[str]):
    if 'question' in file_types:
        file_types.remove('question')
    
    both_ony_worse_idx = []
    if 'summary' in file_types and 'expert' in file_types:
        _, summary_better, summary_worse, summary_same = get_orig_better_worse_same(dirname, 'summary')
        _, expert_better, expert_worse, expert_same = get_orig_better_worse_same(dirname, 'expert')

        summary_worse_idx = summary_worse.index
        expert_worse_idx = expert_worse.index
        both_worse_idx = summary_worse_idx.intersection(expert_worse_idx)

        # Remove problems that had some test cases that were better or worse
        both_ony_worse_idx = both_worse_idx.difference(
            summary_better.index
        ).difference(
            summary_same.index
        ).difference(
            expert_better.index
        ).difference(
            expert_same.index
        )
        print(f'There are {len(both_ony_worse_idx)} both worse problems')

    for ftype in file_types:
        out_path = dirname.joinpath(f'{ftype}_{out_fname}')

        orig, better, worse, same = get_orig_better_worse_same(dirname, ftype)

        # Get the original accuracy
        report_accuracy(orig, out_path, msg='Entire experiment accuracy:\n')

        get_results(better, orig, out_path, ftype,
            msg='problems that got better:\n'
        )

        get_results(same, orig, out_path, ftype,
            msg='problems that stayed the same:\n'
        )
        
        df_out_path = dirname.joinpath(f'{ftype}_new_results_df.csv')
        same_or_better = pd.merge(same, better, how='outer', left_index=True, right_index=True)
        get_results(same_or_better, orig, out_path, ftype,
            msg='problems that got better or stayed the same:\n',
            new_file=df_out_path
        )
        
        get_compare_score(
            better, out_path,
            msg="\nScore difference on problems that got better.\n"
        )

        get_compare_score(
            worse, out_path,
            msg="\nScore difference on problems that got worse.\n"
        )

        if len(both_ony_worse_idx) > 0:
            out_path = dirname.joinpath(f'{ftype}_removed_both_results.txt')
            df_out_path = dirname.joinpath(f'{ftype}_removed_both_df.csv')
            orig = remove_probs(both_ony_worse_idx, orig, ftypes=file_types)

            get_results(orig, orig, out_path, ftype,
                msg='Removing problems that were worse on both\n',
                get_orig=False,
                new_file=df_out_path
            )


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-o', '--output_dir', type=Path, required=True)
    parser.add_argument('-l', '--file_list', nargs='+', required=True)
    args = parser.parse_args()
    print(args)

    out_dir = Path(args.output_dir)
    fname = 'new_results.txt'

    out_fname = out_dir.joinpath(fname)
    main(out_dir, fname, args.file_list)
