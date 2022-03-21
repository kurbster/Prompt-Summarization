#!/usr/bin/env python3
import json
import argparse
import subprocess

from typing import Any, List
from pathlib import Path

try:
    import test_one_solution, codex_results, experiment_results, result_analysis
except ModuleNotFoundError:
    from . import test_one_solution, codex_results, experiment_results, result_analysis

def prepare_agave(dirname: Path):
    path_to_script = Path(__file__, '../../tools/prepare-agave.sh').resolve()
    path_to_json_manifest = Path(dirname, 'test.json')
    subprocess.run([
        path_to_script,
        path_to_json_manifest,
        dirname
    ])

    test_json = read_json(dirname, 'test.json')
    test_json = list(map(
        lambda x: '/scratch/kkuznia' + x.split('data')[-1], test_json
        )
    )
    path_to_json_manifest = Path(dirname, 'agave_test.json')
    with open(path_to_json_manifest, 'w') as f:
        json.dump(test_json, f, indent=4)

def create_test_args(dirname: Path, debug: bool = True) -> list[str]:
    """Create args to pass to test_one_solution.py

    Args:
        dirname (Path): Path to our output dir.
        debug (bool, optional): To include the debug flag or not. Defaults to True.

    Returns:
        list[str]: List of args to be passed.
    """
    arg_arr = [
        '--save', str(dirname),
        '--test_loc', str(dirname / "test.json")
    ]
    if debug:
        arg_arr.append('--debug')
    return arg_arr

def save_json(dirname: Path, obj_to_save: any, fname: str, indent: int = 4) -> None:
    """Save a json object to a file

    Args:
        dirname (Path): The directory to save to.
        obj_to_save (any): The object to save.
        fname (str): The file name to save as.
        indent (int, optional): Indent of the json file. Defaults to 4.
    """
    dir_name = Path(dirname, fname)
    with open(dir_name, 'w') as f:
        json.dump(obj_to_save, f, indent=indent)

def read_json(dirname: Path, fname: str) -> Any:
    fpath = dirname.joinpath(fname)
    with open(fpath) as f:
        result = json.load(f)
    return result

def main(output_dir: Path, file_types: List[str], gen_results: bool=True):
    if gen_results:
        test_arg_arr = create_test_args(output_dir)

        test_args = test_one_solution.parse_args(test_arg_arr)
        test_one_solution.main(test_args)

    results = read_json(output_dir, 'all_results.json')
    test_manifest = read_json(output_dir, 'test.json')

    # Change the format of all_results.json from {'0': [[...]]}
    # To {'path/to/problem/fname.txt': [...]}
    new_results = dict()
    for problem, result in zip(test_manifest, results.values()):
        problem = problem.split('data/')[-1]
        new_results[problem] = result[0]

    save_json(output_dir, new_results, 'results_with_pnames.json', indent=4)
    codex_results.main(new_results, output_dir, file_types)

    experiment_results.main(output_dir, 'new_results.txt', file_types)

    if 'question' in file_types:
        file_types.remove('question')
    for ftype in file_types:
        result_analysis.main(output_dir, ftype=ftype, get_all_results=True)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-o', '--output_dir', type=Path, required=True)
    parser.add_argument('-l', '--file_list', nargs='+', required=True)
    parser.add_argument('--skip-gen', action='store_false')
    args = parser.parse_args()
    print(args)

    output_dir = Path(args.output_dir)
    main(output_dir, args.file_list, gen_results=args.skip_gen)
