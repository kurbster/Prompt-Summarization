#!/usr/bin/env python3
import sys
import json
from typing import List
import hydra
import requests
import logging

from pathlib import Path
from lib.config import APIConfig, ExperimentConfig, Studio21APIConfig, register_configs

from lib.prompt_generation import generate_summary_prompt

logger = logging.getLogger('apiLogger')

def make_prompt(
    token: str,
    cfg: APIConfig,
    sum_type: str,
    prompts: List[str],
    extras: List[str],
    output_dirs: List[str]) -> List[str]:
    """Make a summary using the Studio21 API

    Args:
        token (str): Your api token to use.
        config (ExperimentConfig): Our config object.

    Returns:
        bool: Whether or not to continue calling the api.
    """
    header = {'Authorization': f'Bearer {token}'}
    
    model = cfg.engine

    logger.debug(f'Using model {model} for generation.')
    url = f'https://api.ai21.com/studio/v1/j1-{model}/complete'

    api_cfg = Studio21APIConfig(**cfg)
    api_cfg = api_cfg.convert_to_studio21_kwargs()
    logger.debug(f'Using this studio21 config {api_cfg}')
    
    num_generated = 0
    for prompt, extra, output_dir in zip(prompts, extras, output_dirs):
        data = {'prompt': prompt, **api_cfg}
    
        result = requests.post(url, headers=header, json=data)
        if result.status_code >= 400:
            logger.critical(f'API request error!!! {result.status_code}: {result.text} {result.reason}')
            return num_generated
        else:
            result_json = result.json()
            text = result_json['completions'][0]['data']['text']
            with open(output_dir+'/output.json', 'w') as f:
                json.dump(result_json, f, indent=4)
            with open(f'{output_dir}/{sum_type}.txt', 'w') as f:
                f.write(text+'\n'+extra)
            with open(f'{output_dir}/input_to_studio21.txt', 'w') as f:
                f.write(prompt)
            
            num_generated += 1
    
    return num_generated

@hydra.main(config_path="configs", config_name="studio21")
def main(cfg: ExperimentConfig):
    prompts, extras, output_dirs = generate_summary_prompt(cfg.generation_params)

    logger.info('Running in multiple mode. Using all api keys in .env/studio21_api_keys')
    path_to_env = Path(__file__, '../.env/studio21_api_keys').resolve()

    with open(path_to_env) as f:
        keys = f.readlines()

    total_generated = 0
    for key in keys:
        key = key.strip()
        if not key.startswith('#'):
            if key.startswith('export'):
                key = key.split('=')[1]
            logger.info(f'Running with API key: {key}')
            total_generated += make_prompt(
                key,
                cfg.api_params,
                cfg.generation_params.summary_types[0],
                prompts[total_generated:],
                extras[total_generated:],
                output_dirs[total_generated:]
            )
            
            if total_generated == len(prompts):
                break

if __name__ == '__main__':
    register_configs()
    main()
