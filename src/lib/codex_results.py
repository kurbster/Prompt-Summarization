#!/usr/bin/env python3
import os
import json
import itertools
import pandas as pd

from pathlib import Path

def split_prob(prob, keep_filename=True):
    tmp = prob.split('Prompt-Summarization/data/')[-1]
    if keep_filename:
        return tmp
    return os.path.split(tmp)[0]

def detect_difficulty(prompt):
    difficulty = ['introductory', 'interview', 'competition']
    for d in difficulty:
        if d in prompt:
            return d

def detect_test(prompt):
    if 'test' in prompt:
        return 'test'
    return 'train'
    
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

def main():
    out_file = open('outfile', 'w')
    results = json.load(open('./meta.json'))
    acc = count_results(results)
    print(acc)

    acc_df = acc.copy(deep=False)
    total_acc, strict = get_accuracy(acc_df)
    acc_df.to_csv(out_file, index_label='Problem Names', float_format='%.2f')
    out_file.write(f'\nTotal Accuracy: {total_acc:.2f}%\n')
    out_file.write(f'Strict Accuracy: {strict:.2f}%\n\n')

    out_file.write('Accuracy when grouped by difficulty.\n')
    difficulty = acc.groupby(detect_difficulty).sum()
    total_acc, strict = get_accuracy(difficulty)
    difficulty.to_csv(out_file, index_label='Problem Names', float_format='%.2f')

    out_file.write('\nAccuracy when grouped by the test/train split.\n')
    test_df = acc.groupby(detect_test).sum()
    total_acc, strict = get_accuracy(test_df)
    test_df.to_csv(out_file, index_label='Problem Names', float_format='%.2f')

    better, worse, same = compare_results(results)
    out_file.write('\nProblems that performed better\n')
    better.to_csv(out_file, index_label='Problem Names', float_format='%.2f')
    
    out_file.write('\nProblems that performed worse\n')
    worse.to_csv(out_file, index_label='Problem Names', float_format='%.2f')
    
    out_file.write('\nProblems that performed the same\n')
    same.to_csv(out_file, index_label='Problem Names', float_format='%.2f')

    out_file.close()

if __name__ == '__main__':
    main()