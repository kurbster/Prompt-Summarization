#!/usr/bin/env python3
import os
import sys
sys.path.append('..')
import yaml
import json
import shutil
import openai
import logging

from datetime import datetime
from pathlib import Path

import lib.my_logger

from lib import test_one_solution
from lib.prompt_generation import generate_code_prompt, find_path_to_cfg

logger = logging.getLogger('apiLogger')

path_to_src = Path(__file__, '..')

@find_path_to_cfg
def get_summary(prompts: list[str], config: str) -> dict[str, any]:
    """Call the OpenAI API with the prompts given.

    Args:
        prompts (list[str]): The prompts to send to the API.
        codex_cfg (str): The config file for the API.

    Returns:
        dict[str, any]: The response object.
    """
    with open(config) as f:
        cfg = yaml.safe_load(f)
    api_settings = cfg['apiSettings']
    logger.info(f'Using codex model: {api_settings["engine"]}')
    
    API_KEY = os.getenv("OPENAI_API_KEY")
    logger.info(f'using apikey: {API_KEY}')
    openai.api_key = API_KEY

    response = openai.Completion.create(
        prompt=prompts,
        **api_settings
    )
    
    return response

def create_experiment_dir() -> Path:
    """Create a experiment dir to save results.

    Returns:
        Path: The path to the new dir.
    """
    fname = datetime.now().strftime('%m-%d-%Y/%H_%M')
    dir_path = path_to_src.joinpath('../data/experiments', fname).resolve()
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

if __name__ == "__main__":
    cfg_file = 'codex_config.yaml'
    prompts, output_dirs = generate_code_prompt(config=cfg_file)

    response = get_summary(prompts, cfg_file)

    dirname = create_experiment_dir()
    codes = {str(k): v for k, v in enumerate([val["text"] for val in response["choices"]])}
    prompt_json = {str(k): v for k, v in enumerate(prompts)}

    logger.info(f'Created dir {dirname} for saving results.')
    save_json(dirname, output_dirs, 'test.json')    # List of problems
    save_json(dirname, response, 'response.json')   # Full GPT response
    save_json(dirname, codes, 'all_codes.json')     # Code dict 
    save_json(dirname, prompt_json, 'prompts.json') # Prompts given

    shutil.copy(cfg_file, dirname)

    test_arg_arr = create_test_args(dirname)

    test_args = test_one_solution.parse_args(test_arg_arr)
    test_one_solution.main(test_args)