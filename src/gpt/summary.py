#!/usr/bin/env python3
import os
import sys
sys.path.append('..')
import yaml
import openai
import logging

from datetime import datetime
from pathlib import Path

import my_logger

logger = logging.getLogger('apiLogger')

from prompt_generation import generate_code_prompt

def get_summary(prompts, settings_file, fine_tuned_model=None):
    openai.api_key = os.getenv("OPENAI_API_KEY")

    with open(settings_file) as file:
        GPT_settings = yaml.safe_load(file)

    # Use our model instead of the pretrained ones
    if fine_tuned_model:
        GPT_settings.pop('engine')
        GPT_settings['model'] = fine_tuned_model

    #response = openai.Completion.create(
    #    prompt=prompts,
    #    **GPT_settings
    #)
    #return [val["text"] for val in response["choices"]]
    return 'Hello World'

def save_code(responses, destinations):
    for res, dst in zip(responses, destinations):
        with open(destinations, 'w') as f:
            f.write(res)

def create_experiment_dir():
    root = '../../data/experiments'
    fname = datetime.now().strftime('%m-%d-%Y/%H_%M')
    dir_path = Path(root).joinpath(fname)
    dir_path.mkdir(parents=True, exist_ok=False)

if __name__ == "__main__":
    #create_experiment_dir()
    logger.info(f'using apikey: {os.getenv("OPENAI_API_KEY")}')
    generation_config = 'config.yaml'
    prompts, output_dirs = generate_code_prompt(config=generation_config)

    if len(sys.argv) > 1:
        model = sys.argv[1]
        logger.info(f'Using fine tuned model: {model}')
        summaries = get_summary(prompts, "./api_settings.yaml", fine_tuned_model=model)
    else:
        logger.info(f'Using pretrained model defined in settings.yaml')
        summaries = get_summary(prompts, "./api_settings.yaml")
    #logger.debug(summaries)
    for sum in prompts:
        print(sum)

    print(output_dirs)
