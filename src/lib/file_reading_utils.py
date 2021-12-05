#!/usr/bin/env python3
import os
import json
import logging

from pathlib import Path

logger = logging.getLogger('apiLogger')

PATH_TO_EXPERIMENTS = Path(__file__, '../../../data/experiments').resolve()

def split_prob(prob, keep_filename=True):
    tmp = prob.split('data/')[-1]
    if keep_filename:
        return tmp
    return os.path.split(tmp)[0]

def get_result_dict(dir_list):
    test_fname = "test.json"
    result_fname = "all_results.json"
    result_dict = {}

    for dir_path in dir_list:
        dir_path = PATH_TO_EXPERIMENTS.joinpath(dir_path)
        
        # read files
        test_file = dir_path.joinpath(test_fname)
        result_file = dir_path.joinpath(result_fname)

        with open(test_file) as f:
            test_paths = json.load(f)

        with open(result_file) as f:
            result_obj = json.load(f)

        #generate result dict
        for ind, test_path in enumerate(test_paths):
            path = split_prob(test_path)
            logger.info(f"Adding result path: {path}")
            result_dict[path] = result_obj[str(ind)][0]
    return result_dict   

def main(dir_list) -> dict[str, list[any]]:
    if isinstance(dir_list, Path):
        with open(dir_list) as f:
            dir_list = f.read().splitlines()

    res = get_result_dict(dir_list)
    return res

if __name__ == '__main__':
    import sys
    import my_logger
    input_file, output_file = Path(sys.argv[1]), Path(sys.argv[2])
    results = main(input_file)
    with open(output_file, 'w') as f:
        json.dump(results, f) 
else:
    from . import my_logger
