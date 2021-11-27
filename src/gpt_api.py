#!/usr/bin/env python3
import os
import json
import yaml
import openai
import logging

import my_logger
from prompt_generation import generate_prompt

logger = logging.getLogger('apiLogger')

def make_prompt_gpt(config_path):
    with open(config_path) as file:
         cfg = yaml.safe_load(file)
         GPT_settings = cfg["apiParams"]
    prompt, extra, output_dir = generate_prompt("gpt",config = config_path)
    logger.info(f'Saving gpt response in {output_dir}')
    if len(prompt.split(" ")) > 2049:
        raise Exception("prompt length is too long please reduce it")
    API_KEY = os.getenv("OPENAI_API_KEY")
    openai.api_key = API_KEY
    result = openai.Completion.create(
        prompt=[prompt],
        **GPT_settings
    )
    text = result["choices"][0]["text"]
    json.dump(result, open(output_dir+'/output.json', 'w'), indent=4)
    with open(f'{output_dir}/{cfg["summaryType"]}.txt', 'w') as f:
        f.write(text+'\n'+extra)
    with open(f'{output_dir}/input_to_gpt.txt', 'w') as f:
        f.write(prompt)
    
if __name__ == '__main__':
    make_prompt_gpt("config_gpt.yaml")