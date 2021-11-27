#!/usr/bin/env python3
import os
import json
import yaml
import openai
import logging

from pathlib import Path

import lib.my_logger
from lib.prompt_generation import generate_summary_prompt, find_path_to_cfg

logger = logging.getLogger('apiLogger')

@find_path_to_cfg
def make_prompt_gpt(config: Path):
    """Make a summary using GPT.

    Args:
        config (Path): Path to the config file.

    Raises:
        Exception: If your prompt is too long.
    """
    with open(config) as file:
        cfg = yaml.safe_load(file)
    GPT_settings = cfg["apiParams"]

    cfg_name = os.path.basename(config)
    prompt, extra, output_dir = generate_summary_prompt("gpt",config=cfg_name)
    logger.info(f'Saving gpt response in {output_dir}')

    if len(prompt.split(" ")) > 2049:
        raise Exception("prompt length is too long please reduce it")

    API_KEY = os.getenv("OPENAI_API_KEY")
    openai.api_key = API_KEY
    result = openai.Completion.create(
        prompt=[prompt],
        **GPT_settings
    )
    
    json.dump(result, open(output_dir+'/output.json', 'w'), indent=4)

    text = result["choices"][0]["text"]
    with open(f'{output_dir}/{cfg["summaryType"]}.txt', 'w') as f:
        f.write(text+'\n'+extra)
    with open(f'{output_dir}/input_to_gpt.txt', 'w') as f:
        f.write(prompt)
    
if __name__ == '__main__':
    make_prompt_gpt("gpt_config.yaml")