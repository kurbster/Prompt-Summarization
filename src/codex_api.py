#!/usr/bin/env python3
import os
import sys
import yaml
import json
import time
import shutil
import openai
import logging

from datetime import datetime
from pathlib import Path
from openai.error import RateLimitError

import lib.my_logger

from lib import test_one_solution, file_reading_utils, codex_results
from lib.prompt_generation import generate_code_prompt, find_path_to_cfg

logger = logging.getLogger('apiLogger')

PATH_TO_EXP = Path(__file__, '../../data/experiments').resolve()

@find_path_to_cfg
def get_codes(prompts: list[str], config: Path) -> dict[str, any]:
    """Call the OpenAI API with the prompts given.

    Args:
        prompts (list[str]): The prompts to send to the API.
        codex_cfg (Path): The config file for the API.

    Returns:
        dict[str, any]: The response object.
    """
    with open(config) as f:
        cfg = yaml.safe_load(f)
    api_settings = cfg['apiParams']
    logger.info(f'Using codex model: {api_settings["engine"]}')
    
    API_KEY = os.getenv("OPENAI_API_KEY")
    logger.info(f'using apikey: {API_KEY}')
    openai.api_key = API_KEY

    try:
        response = openai.Completion.create(
            prompt=prompts,
            **api_settings
        )
    # We have exceeded OpenAIs rate limit of 150,000 tokens/min
    # We need to cleep for a minute then try again
    except RateLimitError:
        logger.error('We have hit our rate limit. Sleeping for a minute...')
        time.sleep(60)
        response = openai.Completion.create(
            prompt=prompts,
            **api_settings
        )
        
    return response

def create_experiment_dir(path_to_exp: Path) -> Path:
    """Create a experiment dir to save results.

    Args:
        path_to_exp (Path): Path to the experiments dir.
    
    Returns:
        Path: The path to the new dir.
    """
    fname = datetime.now().strftime('%m-%d-%Y/%H_%M_%S')
    dir_path = path_to_exp.joinpath(fname)
    dir_path.mkdir(parents=True, exist_ok=False)
    return dir_path

def save_json(dirname: Path, obj_to_save: any, fname: str, indent: int = 4) -> None:
    """Save a json object to a file

    Args:
        dirname (Path): The directory to save to.
        obj_to_save (any): The object to save.
        fname (str): The file name to save as.
        indent (int, optional): Indent of the json file. Defaults to 4.
    """
    dir_name = os.path.join(dirname, fname)
    with open(dir_name, 'w') as f:
        json.dump(obj_to_save, f, indent=indent)

def clean_codes(codes: dict[str, str]) -> dict[str, str]:
    """We need to remove any call codex makes to the function
    it created. If not the testing module breaks.

    Args:
        codes (dict[str, str]): The codes produced by Codex.

    Returns:
        dict[str, str]: The cleaned codes.
    """
    result = {}
    for idx, code in codes.items():
        # if name main isn't causing issues. Only if
        # The function created is called. So only remove
        # The last function call if it is not inside if name main
        main_idx = code.find('if __name__')
        if main_idx == -1 and code.endswith('()'):
            # remove last line
            code_arr = code.split('\n')[:-1]
            code = '\n'.join(code_arr)
        result[idx] = code
    return result

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

@find_path_to_cfg
def save_config(dirname: Path, config: Path) -> None:
    shutil.copy(config, dirname)

def main(prompts: list[str], prompt_files: list[str], cfg_file: str):
    response = get_codes(prompts, cfg_file)

    dirname = create_experiment_dir(PATH_TO_EXP)

    codes = {str(k): v for k, v in enumerate([val["text"] for val in response["choices"]])}
    codes = clean_codes(codes)

    prompt_json = {str(k): v for k, v in enumerate(prompts)}

    save_json(dirname, prompt_files, 'test.json')   # List of problems
    save_json(dirname, response, 'response.json')   # Full GPT response
    save_json(dirname, codes, 'all_codes.json')     # Code dict 
    save_json(dirname, prompt_json, 'prompts.json') # Prompts given
    save_config(dirname, cfg_file)                  # Config file

    test_arg_arr = create_test_args(dirname)

    test_args = test_one_solution.parse_args(test_arg_arr)
    test_one_solution.main(test_args)

    logger.info(f'Saved results here: {dirname}')
    return dirname

if __name__ == "__main__":
    cfg_file = 'codex_config.yaml'
    prompts, prompt_files = generate_code_prompt(config=cfg_file)

    experiments_list = []
    # Can send max of 20 prompts to codex at a time
    for i in range(0, len(prompts), 20):
        logger.info(f'Generating code for problems {i} through {i+20}')
        exp_dir = main(
            prompts[i:i+20],
            prompt_files[i:i+20],
            cfg_file)
        experiments_list.append(exp_dir)

    results = file_reading_utils.main(experiments_list)
    
    path_to_exp_agg = PATH_TO_EXP.joinpath('aggregate_results')
    exp_dir = create_experiment_dir(path_to_exp_agg)
    json_file = exp_dir.joinpath('all_results.json')

    with open(json_file, 'w') as f:
        json.dump(results, f)

    codex_results.main(results, exp_dir)

    logger.info(f'Saved final results here {exp_dir}')