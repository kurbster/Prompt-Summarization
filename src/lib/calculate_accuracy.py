#!/usr/bin/env python3
import json
import argparse

from pathlib import Path
from typing import Dict, List, Tuple

import pandas as pd

# Results is a dict like: {"0": [[-1, -1, false, true]]}
# But when reading we remove the outer list and cast to int.
ResultType = Dict[str, List[int]]

def read_result_file(args) -> ResultType:
    """Read the result file output by the test_one_solution.py script."""
    result_file = args.results_file
    if not result_file.exists():
        raise ValueError(f"The result file '{result_file}' did not exist!")
    with open(result_file) as f:
        results = json.load(f)
    return clean_results(results)

def clean_results(results: ResultType):
    """Remove the unnecessary outer list in the dictionary."""
    return {k: [int(i) for i in v[0]] for k, v in results.items()}

def get_output_dir(args) -> Path:
    """Ensure the output dir exists and return path."""
    output_dir = args.results_file.parent
    if args.output_dir is not None:
        output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir
    
def calculate_scores(results: ResultType) -> pd.DataFrame:
    """Count the unit test results for each problem."""
    df = pd.DataFrame(0, index=results.keys(), columns=[-2, -1, 0, 1])
    for problem, res in results.items():
        for r in res:
            df.loc[problem, r] +=1
    return df

def calculate_accuracy(scores: pd.DataFrame) -> Tuple[float, float]:
    """Calculate the raw accuracy (correct test cases / total test cases).
    And strict accuracy (# problems with 100% test accuracy / # problems).  """
    summed_scores = scores.sum()
    correct = summed_scores[1]
    total = summed_scores.sum()
    acc = 100 * correct / total

    # Count number of problems that had no -2, -1, 0 outcomes
    problems_all_correct = (scores[[-2, -1, 0]] == 0).all(axis=1).sum()
    strict_accuracy = 100 * (problems_all_correct / len(scores.index))
    return acc, strict_accuracy, summed_scores

def output_results(scores: pd.DataFrame, output_dir: Path):
    def get_experiment_name(name):
        return name.split("/")[-1]

    exp_groups = scores.groupby(get_experiment_name).groups
    for group, idx in exp_groups.items():
        accuracy, strict_accuracy, summed_scores = calculate_accuracy(scores.loc[idx])
        print(f"Results for experiment {group}")
        print("-"*80)
        print(f"{summed_scores.sum()} total problems scored.")
        print(f"Number of compile errors = {summed_scores[-2]}")
        print(f"Number of runtime errors = {summed_scores[-1]}")
        print(f"Number of unit test failures = {summed_scores[0]}")
        print(f"Number of unit test passes = {summed_scores[1]}")
        print(f"Raw Accuracy: {accuracy:.5f}")
        print(f"Strict Accuracy: {strict_accuracy:.5f}")
        print("-"*80)

    output_fname = output_dir / "results.csv"
    scores.to_csv(output_fname, index_label="Problem")

def print_results(results: ResultType, output_dir: Path):
    results = clean_results(results)
    scores = calculate_scores(results)
    output_results(scores, output_dir)

def main(args):
    results = read_result_file(args)
    output_dir = get_output_dir(args)
    scores = calculate_scores(results)
    output_results(scores, output_dir)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'results_file', type=Path,
        help=(
            "This should be the fpath to the 'all_results.json' file "
            "produced by the 'test_one_solution.py' script."
        )
    )
    parser.add_argument(
        '-o', '--output_dir', type=Path,
        help=(
            "This is the path to the directory you would like the output "
            "to be written to. A 'results.csv' file will be created in this "
            "directory. This argument is not required and by default will be "
            "the same directory as the 'all_results.json' file."
        )
    )
    args = parser.parse_args()
    main(args)
