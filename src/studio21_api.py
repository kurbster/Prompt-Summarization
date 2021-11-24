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
from lib.prompt_generation import generate_summary_prompt

logger = logging.getLogger('apiLogger')

def make_prompt(token: str, cfg_file: str, model: str = ''):
    header = {'Authorization': f'Bearer {token}'}
    
    with open(cfg_file) as f:
        cfg = yaml.safe_load(f)

    if not model:
        model = cfg['model']
    # If model was passed, set in the config for saving later.
    else:
        cfg['model'] = model

    logger.debug(f'Using model {model} for generation.')
    url = f'https://api.ai21.com/studio/v1/j1-{model}/complete'

    prompt, extra, output_dir = generate_summary_prompt('studio21', config=cfg_file)

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
    
    path_to_src = Path(__file__, '..')
    path_to_cfg = path_to_src.joinpath('configs/studio21_config.yaml').resolve()

    if args.single:
        logger.info('Running in single mode. Only using 1 api key.')
        key = os.getenv('STUDIO21_API_KEY')
        logger.info(f'Running with API key: {key}')
        while make_prompt(token=key, cfg_file=path_to_cfg):
            pass
    else:
        logger.info('Running in multiple mode. Using all api keys in .env/studio21_api_keys')
        path_to_env = path_to_src.joinpath('.env/studio21_api_keys').resolve()
        with open(path_to_env) as f:
            keys = f.readlines()
        for key in keys:
            key = key.strip()
            if not key.startswith('#'):
                if key.startswith('export'):
                    key = key.split('=')[1]
                logger.info(f'Running with API key: {key}')
                main(token=key, cfg_file=path_to_cfg, model='large')
                main(token=key, cfg_file=path_to_cfg, model='jumbo')

if __name__ == '__main__':
    main(sys.argv[1:])
