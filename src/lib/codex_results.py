#!/usr/bin/env python3
import os
import json
import itertools
import pandas as pd

from pathlib import Path
from typing import TextIO, Callable

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
    correct = df[True].sum()
    total   = df.sum().sum()
    acc = 100 * correct/total
    df['acc'] = 100 * df[True]/df.sum(axis=1)
    strict_acc = 100 * sum(df['acc'] >= 100)/len(df)
    return acc, strict_acc

def compare_results(results):
    orig_probs = list(results.keys())
    probs = {split_prob(p, keep_filename=False) for p in orig_probs}

    cols = list(itertools.product(
        ['-2=>', '-1=>', 'False=>', 'True=>'],
        ['-2', '-1', 'False', 'True']))
    cols = [''.join(c) for c in cols]

    better = pd.DataFrame(0, index=probs, columns=cols)
    worse = pd.DataFrame(0, index=probs, columns=cols)
    same = pd.DataFrame(0, index=probs, columns=cols)

    itr = iter(results.items())
    for k1, v1 in itr:
        _, v2 = next(itr)
        # Check which prompt in the pair is the summary.
        if k1.endswith('expert.txt'):
            summary = v1
            original = v2
        else:
            summary = v2
            original = v1

        # The len is different if one had a -2 error.
        if len(original) < len(summary):
            original *= len(summary)
        if len(original) > len(summary):
            summary *= len(original)

        num = split_prob(k1, keep_filename=False)
        for orig, summ in zip(original, summary):
            col = f'{orig}=>{summ}'
            if summ > orig:
                better.loc[num, col] += 1
            elif summ < orig:
                worse.loc[num, col] += 1
            else:
                same.loc[num, col] += 1
    
    better = better.loc[:, ~(better==0).all()]
    worse = worse.loc[:, ~(worse==0).all()]
    same = same.loc[:, ~(same==0).all()]
    return better, worse, same

def agg_results(df: pd.DataFrame, func: Callable, out_file: TextIO, msg: str = '', new_file: Path = None):
    # Get the scrict accuracy before adding the real accuracy
    strict_acc = df.copy(deep=False)
    get_accuracy(strict_acc)
    strict_acc = strict_acc['acc'] >= 100
    strict_acc = 100 * strict_acc.groupby(func).mean()

    df = df.groupby(func).sum()
    get_accuracy(df)
    df['strict acc'] = strict_acc
    write_df(df, out_file, msg=msg, new_file=new_file)

def write_df(df: pd.DataFrame, out_file: TextIO, msg: str = '', new_file: Path = None):
    write_msg(out_file, msg)
    df.to_csv(out_file, index_label='Problem Names', float_format='%.2f')
    if new_file:
        with open(new_file, 'w') as f:
            df.to_csv(f, index_label='Problem Names', float_format='%.2f')

def write_msg(out_file, msg):
    if msg:
        out_file.write(msg)
        out_file.write('\n')

def main(results: dict[str, list[any]], out_dir: Path):
    out_fname = out_dir.joinpath('codex_results.txt')
    out_file = open(out_fname, 'w')

    acc = count_results(results)
    acc_df = acc.copy(deep=False)

    total_acc, strict = get_accuracy(acc_df)
    write_df(acc_df, out_file, new_file=out_dir.joinpath('original_df.csv'))

    out_file.write(f'\nTotal Accuracy: {total_acc:.2f}%\n')
    out_file.write(f'Strict Accuracy: {strict:.2f}%\n\n')

    agg_results(
        acc, detect_summary, out_file,
        msg='Accuracy when grouped by original and summary.',
        new_file=out_dir.joinpath('summary_vs_orig_df.csv'))

    agg_results(
        acc, detect_difficulty, out_file,
        msg='\nAccuracy when grouped by difficulty.',
        new_file=out_dir.joinpath('difficulty_df.csv'))

    agg_results(
        acc, detect_test, out_file,
        msg='\nAccuracy when grouped by the test/train split.',
        new_file=out_dir.joinpath('train_test_df.csv'))

    better, worse, same = compare_results(results)

    write_df(
        better, out_file,
        msg='\nProblems that performed better',
        new_file=out_dir.joinpath('better_df.csv'))
    write_df(
        worse, out_file,
        msg='\nProblems that performed worse',
        new_file=out_dir.joinpath('worse_df.csv'))
    write_df(
        same, out_file,
        msg='\nProblems that performed the same',
        new_file=out_dir.joinpath('same_df.csv'))

    out_file.close()

if __name__ == '__main__':
    import sys
    input_file, output_file = sys.argv[1:3]
    res = json.load(open(input_file))
    out_fpath = Path(output_file)
    main(res, out_fpath)