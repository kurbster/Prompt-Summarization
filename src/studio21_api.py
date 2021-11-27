#!/usr/bin/env python3
import os
import sys
import json
import yaml
import requests
import logging
import argparse

from pathlib import Path

import lib.my_logger
from lib.prompt_generation import find_path_to_cfg, generate_summary_prompt

logger = logging.getLogger('apiLogger')

@find_path_to_cfg
def make_prompt(token: str, config: Path, model: str = ''):
    """Make a summary using the Studio21 API

    Args:
        token (str): Your api token to use.
        config (Path): The path to the config file.
        model (str, optional): Which model to use. If empty
        then read the model from the config file. Defaults to ''.

    Returns:
        bool: Whether or not to continue calling the api.
    """
    header = {'Authorization': f'Bearer {token}'}
    
    with open(config) as f:
        cfg = yaml.safe_load(f)

    if not model:
        model = cfg['model']

    logger.debug(f'Using model {model} for generation.')
    url = f'https://api.ai21.com/studio/v1/j1-{model}/complete'
    
    cfg_name = os.path.basename(config)
    prompt, extra, output_dir = generate_summary_prompt('studio21', config=cfg_name)

    # If the prompt is over 1900 tokens we will most likely get
    # An API error. The model can only take 2048 tokens.
    prompt_tokens = len(prompt.split())
    if prompt_tokens > 1800:
        logger.warning(f'Our prompt was too long. Had {prompt_tokens} tokens.')
        return True
    else:
        logger.debug(f'Our prompt had {prompt_tokens} tokens.')

    data = {'prompt': prompt, **cfg['apiParams']}

    result = requests.post(url, headers=header, json=data)
    if result.status_code >= 400:
        logger.critical(f'API request error!!! {result.status_code}: {result.text} {result.reason}')
        # A 429 status code means we have reached our quota. So we return false.
        # Any other code we ignore and continue.
        return result.status_code != 429
    else:
        text = result.json()['completions'][0]['data']['text']
        json.dump(result.json(), open(output_dir+'/output.json', 'w'), indent=4)
        with open(f'{output_dir}/{cfg["summaryType"]}.txt', 'w') as f:
            f.write(text+'\n'+extra)

    return True 

def main(argv):
    parser = argparse.ArgumentParser(description="Choose how to run the Studio21 API")
    parser.add_argument('-s', '--single', action='store_true', help="""If included then
    only read 1 api from os.getenv""")

    args = parser.parse_args(argv)
    
    cfg_file = 'studio21_config.yaml'

    if args.single:
        logger.info('Running in single mode. Only using 1 api key.')
        key = os.getenv('STUDIO21_API_KEY')
        logger.info(f'Running with API key: {key}')
        while make_prompt(token=key, config=cfg_file):
            pass
    else:
        logger.info('Running in multiple mode. Using all api keys in .env/studio21_api_keys')
        path_to_env = Path(__file__, '../.env/studio21_api_keys').resolve()
        with open(path_to_env) as f:
            keys = f.readlines()
        for key in keys:
            key = key.strip()
            if not key.startswith('#'):
                if key.startswith('export'):
                    key = key.split('=')[1]
                logger.info(f'Running with API key: {key}')
                make_prompt(token=key, config=cfg_file, model='large')
                make_prompt(token=key, config=cfg_file, model='jumbo')

if __name__ == '__main__':
    main(sys.argv[1:])
