#!/usr/bin/env python3
import json
import yaml
import requests
import logging

from prompt_generation import generate_prompt

logger = logging.getLogger('apiLogger')

def make_prompt(token, model):
    header = {'Authorization': f'Bearer {token}'}
    
    url = f'https://api.ai21.com/studio/v1/j1-{model}/complete'

    prompt, extra, output_dir = generate_prompt('config.yaml')

    # If the prompt is over 1900 tokens we will most likely get
    # An API error. The model can only take 2048 tokens.
    prompt_tokens = len(prompt.split())
    if prompt_tokens > 1800:
        print(f'Our prompt was too long. Had {prompt_tokens} tokens.')
        return True

    with open('config.yaml') as f:
        cfg = yaml.safe_load(f)
    data = {'prompt': prompt, **cfg['apiParams']}

    result = requests.post(url, headers=header, json=data)
    if result.status_code >= 400:
        print('API request error!!!')
        print(result.status_code)
        print(result.text)
        print(result.reason)
        # A 429 status code means we have reached our quota. So we return false.
        # Any other code we ignore and continue.
        return result.status_code != 429
    else:
        text = result.json()['completions'][0]['data']['text']
        json.dump(result.json(), open(output_dir+'/output.json', 'w'), indent=4)
        with open(f'{output_dir}/{cfg.summaryType}.txt', 'w') as f:
            f.write(text+'\n'+extra)

    return True

def main(*a, **kw):
    while make_prompt(*a, **kw):
        pass

if __name__ == '__main__':
    with open('./api_keys') as f:
        keys = f.readlines()
    for key in keys:
        key = key.strip()
        print(f'\n\n\nRUNNING WITH API KEY == {key}\n\n\n')
        if not key.startswith('#'):
            main(token=key, model='large')
            main(token=key, model='jumbo')