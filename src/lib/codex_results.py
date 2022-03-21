#!/usr/bin/env python3
import os
import json
import logging
import argparse
import itertools
import pandas as pd

from pathlib import Path
from typing import Dict, List, TextIO, Callable
from argparse import RawTextHelpFormatter

logger = logging.getLogger('apiLogger')

def split_prob(prob, keep_filename=True):
    tmp = prob.split('Prompt-Summarization/data/')[-1]
    if keep_filename:
        return tmp
    return os.path.split(tmp)[0]

def detect_summary(prompt):
    summary = os.path.split(prompt)[-1]
    summary = os.path.splitext(summary)[0]
    return summary

def detect_difficulty(prompt):
    difficulty = ['competition', 'interview', 'introductory']
    summary = detect_summary(prompt)
    for d in difficulty:
        if d in prompt:
            return f'{d}-{summary}'

def detect_test(prompt):
    summary = detect_summary(prompt)
    if 'test' in prompt:
        return f'test-{summary}'
    return f'train-{summary}'
    
def count_results(results: dict[str, dict[str, list[any]]]) -> pd.DataFrame:
    df = pd.DataFrame(0, index=results.keys(), columns=[-2, -1, False, True])
    for prompt, res in results.items():
        for r in res:
            df.loc[prompt, r] +=1
    return df

def get_accuracy(df: pd.DataFrame) -> None:
    data = df.copy(deep=False)
    # Don't take score column when getting accuracy
    if 'score' in data:
        data = data.drop('score', axis=1)
    summed = data.sum()
    correct = summed[True]
    total = summed.sum()
    acc = 100 * correct/total
    df['acc'] = 100 * data[True]/data.sum(axis=1)
    strict_acc = 100 * sum(df['acc'] >= 100)/len(df)
    return acc, strict_acc

def compare_results(results: Dict[str, List[any]], file_type: str):
    orig_probs = list(results.keys())
    probs = {split_prob(p, keep_filename=False) for p in orig_probs}

    possible_vals = ['-2', '-1', 'False', 'True']
    cols = list(itertools.product(possible_vals, possible_vals))
    cols = ['=>'.join(c) for c in cols]

    better = pd.DataFrame(0, index=probs, columns=cols)
    worse = pd.DataFrame(0, index=probs, columns=cols)
    same = pd.DataFrame(0, index=probs, columns=cols)

    for problem in probs:
        new_file = f'{problem}/{file_type}.txt'
        orig_file = f'{problem}/question.txt'
        new_results = results[new_file]
        orig_results = results[orig_file]

        # The len is different if one had a -2 error.
        if len(orig_results) < len(new_results):
            orig_results *= len(new_results)
        if len(orig_results) > len(new_results):
            new_results *= len(orig_results)

        for orig, summ in zip(orig_results, new_results):
            col = f'{orig}=>{summ}'
            if summ > orig:
                better.loc[problem, col] += 1
            elif summ < orig:
                worse.loc[problem, col] += 1
            else:
                same.loc[problem, col] += 1

    same = same.loc[(same!=0).any(axis=1), (same!=0).any()]
    worse = worse.loc[(worse!=0).any(axis=1), (worse!=0).any()]
    better = better.loc[(better!=0).any(axis=1), (better!=0).any()]

    return better, worse, same

def agg_results(df: pd.DataFrame, func: Callable, out_file: TextIO, msg: str = '', new_file: Path = None):
    data = df.copy(deep=False)
    # Get the scrict accuracy before adding the real accuracy
    strict_acc = df.copy(deep=False)
    get_accuracy(strict_acc)
    strict_acc = strict_acc['acc'] >= 100
    strict_acc = 100 * strict_acc.groupby(func).mean()

    scores = [-2, -1, 0, 1]
    data['score'] = data.mul(scores).sum(axis=1)

    grouped = data.groupby(func)
    data = grouped.sum()
    get_accuracy(data)
    data['strict acc'] = strict_acc
    data['Num Probs'] = grouped[True].count()
    write_df(data, out_file, msg=msg, new_file=new_file)
    return data

def write_df(df: pd.DataFrame, out_file: TextIO, idx_label='Problem Names', msg: str = '', new_file: Path = None):
    write_msg(out_file, msg)
    df.to_csv(out_file, index_label=idx_label, float_format='%.2f')
    if new_file:
        with open(new_file, 'w') as f:
            df.to_csv(f, index_label=idx_label, float_format='%.2f')

def write_msg(out_file, msg):
    if msg:
        out_file.write(msg)
        out_file.write('\n')

def main(results: Dict[str, List[any]], out_dir: Path, file_types: List[str]):
    out_fname = out_dir.joinpath('codex_results.txt')
    out_file = open(out_fname, 'w')

    acc = count_results(results)
    acc_df = acc.copy(deep=False)

    total_acc, strict = get_accuracy(acc_df)
    logger.info(f'Total accuracy: {total_acc}')
    logger.info(f'Strict accuracy: {strict}')
    write_df(acc_df, out_file, new_file=out_dir.joinpath('original_df.csv'))

    out_file.write(f'\nTotal Accuracy: {total_acc:.2f}%\n')
    out_file.write(f'Strict Accuracy: {strict:.2f}%\n\n')

    agg_results(
        acc, detect_summary, out_file,
        msg='Accuracy when grouped by original and summary.',
        new_file=out_dir.joinpath('compared_to_original_df.csv'))

    agg_results(
        acc, detect_difficulty, out_file,
        msg='\nAccuracy when grouped by difficulty.',
        new_file=out_dir.joinpath('difficulty_df.csv'))

    agg_results(
        acc, detect_test, out_file,
        msg='\nAccuracy when grouped by the test/train split.',
        new_file=out_dir.joinpath('train_test_df.csv'))

    # If we tested the original question plus another file type
    # Then we should compare the other file type against the original
    if 'question' in file_types and len(file_types) > 1:
        file_types.remove('question')
        for ftype in file_types:
            better, worse, same = compare_results(results, ftype)
            logger.info(f'{len(better)} problems got better for using {ftype}')
            logger.info(f'{len(worse)} problems got worse for using {ftype}')
            logger.info(f'{len(same)} problems stayed the same for using {ftype}')

            write_df(
                better, out_file,
                msg=f'\n{ftype} problems that performed better',
                new_file=out_dir.joinpath(f'{ftype}_better_df.csv'))
            write_df(
                worse, out_file,
                msg=f'\n{ftype} problems that performed worse',
                new_file=out_dir.joinpath(f'{ftype}_worse_df.csv'))
            write_df(
                same, out_file,
                msg=f'\n{ftype} problems that performed the same',
                new_file=out_dir.joinpath(f'{ftype}_same_df.csv'))

    out_file.close()

if __name__ == '__main__':
    doc_str = (
    "Calculate the aggregate metrics for an experiment. This file needs "
    "to be passed the the path to the aggregated all_results.json file. "
    "Along with the path to an output directory to save the results. This "
    "file will create. The following files:\n\tcodex_results.txt - A text "
    "file listing all of the results.\n\tbetter_df.csv - A pandas df that "
    "contains all of the problems that peformed better.\n\tworse_df.csv - "
    "A pandas df that contains all of the problems that peformed worse."
    "\n\tsame_df.csv - A pandas df that contains all of the problems that peformed same."
    "\n\toriginal_df.csv - A pandas df that contains the original data before "
    "grouping the results.\n\tsummary_vs_orig_df.csv - A pandas df that contains the results "
    "grouped by original question vs. the summary.\n\tdifficulty_df.csv - "
    "A pandas df that contains the results when grouped by their difficulty. "
    "\n\ttrain_test_df.csv - A pandas df that contains the results when grouped by "
    "the train or test split."
    )
    parser = argparse.ArgumentParser(description=doc_str, formatter_class=RawTextHelpFormatter)
    parser.add_argument('-o', '--output_dir', type=Path, required=True)
    parser.add_argument('-l', '--file_list', nargs='+', required=True)
    args = parser.parse_args()
    print(args)

    output_dir = Path(args.output_dir)
    results_path = output_dir.joinpath('results_with_pnames.json')
    with open(results_path) as f:
        results = json.load(f)

    main(results, output_dir, args.file_list)
