#!/usr/bin/env python3
import os
import json
import glob
import shutil
import random
import requests

from omegaconf import OmegaConf

def get_prompt(cfg: OmegaConf) -> str:
    # Get the problems we have already done
    probs = glob.glob('../[ic]*/*')
    model_probs = glob.glob('../model_generated/[ic]*/*')

    probs = [os.path.basename(p) for p in probs]
    model_probs = [os.path.basename(p) for p in model_probs]

    prompt, output_dir = select_summary_prompt(probs+model_probs)
    
    # Save config in output dir
    fname = output_dir + '/config.yaml'
    OmegaConf.save(config=cfg, f=fname)
    shutil.copy(cfg.promptFile, output_dir)

    # TODO: Get the problem category
    prompt_type = detect_type(prompt)
    
    # This is the prompt we want to summarize
    prompt, remainder = split_question(prompt)
    
    # The priming prompt is the header plus our generated examples.
    priming_prompts = [cfg.header]
    priming_prompts = priming_prompts + generate_example_prompt(prompt_type, cfg, probs)

    final_prompt = '\n\n'.join(priming_prompts) + f'\n\nJargon: {prompt}\nSimple:'

    # We must return the remainder to append it to the output file
    return final_prompt, remainder, output_dir

def generate_example_prompt(prompt_type: str, cfg: OmegaConf, probs: list[str]) -> str:
    prompt_cfg = OmegaConf.load(cfg.promptFile)
    output = []
    # If it's a general problem choose any examples
    if prompt_type == 'general':
        example_prompts = random.sample(probs, cfg.numPrompts)

    example_prompts = ['2537', '2200', '0443', '2000', '0205']
    for ex in example_prompts:
        # Get the original prompt and the summarized
        orig = glob.glob(f'../[ic]*/{ex}/question.txt')[0]
        example = glob.glob(f'../[ic]*/{ex}/{cfg.summaryType}.txt')[0]
        print(f'Using summary {example} for priming model')
        orig, _ = split_question(orig)
        example, _ = split_question(example)
        output.append(f'Jargon: {orig}\nSimple: {example}')
    
    return output

def select_summary_prompt(probs: list[str]):
    # Select a random problem to summarize
    total_probs = [str(i).zfill(4) for i in range(5000) if str(i).zfill(4) not in probs]
    assert len(total_probs) + len(probs) == 5000, f'The total probs must add to 5000'
    prob = random.choice(total_probs)

    prob ='0311'

    prompt = glob.glob(f'../APPS/*/{prob}/question.txt')[0]

    # Copy the original directory to the output directory
    prompt_dir = os.path.split(prompt)[0]
    output_dir = prompt_dir.replace('APPS', 'model_generated')
    shutil.copytree(prompt_dir, output_dir)
    return prompt, output_dir

def detect_type(fname: str) -> str:
    print(f'I am the fname {fname}')
    return 'general'

def split_question(fname: str) -> str:
    # Read the prompt
    prompt = []
    with open(fname) as f:
        prompt = f.readlines()
    
    # Strip newlines
    prompt = [p.strip('\n') for p in prompt if p != '\n']
    prompt = ' '.join(prompt)

    # Find the prompt section
    prompt_idx = prompt.find('-----Input')
    if prompt_idx == -1:
        prompt_idx = prompt.find('=====Input')
    if prompt_idx == -1:
        print(f'For file {fname} We did not find a split!!!')
        return prompt, ''
    return prompt[:prompt_idx], prompt[prompt_idx:]
    
def make_prompt():
    TOKEN_LIMITS = {'large': 30000, 'jumbo': 10000}
    cfg = OmegaConf.load('config.yaml')
    
    header = {'Authorization': f'Bearer {cfg.token}'}
    cfg.pop('token')
    
    model = cfg.model
    url = f'https://api.ai21.com/studio/v1/j1-{model}/complete'

    prompt, extra, output_dir = get_prompt(cfg)

    prompt_dict = {'prompt': prompt}
    #print(cfg)
    api_cfg = OmegaConf.merge(cfg.apiParams, prompt_dict)
    api_cfg = OmegaConf.to_container(api_cfg)
    data = {**api_cfg}

    result = requests.post(url, headers=header, json=data)
    if result.status_code >= 400:
        tokens_used = len(prompt.split())
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

        # Update the token usage this is a rough estimate
        tokens_used = len(prompt.split()) + len(text.split())
        print(f'Tokens used this run ~= {tokens_used}')
        usage = OmegaConf.load('usage.yaml')

        # Account for some error in calculating num tokens
        usage[model] += int(tokens_used * 1.15)
        OmegaConf.save(config=usage, f='usage.yaml')

    return usage[model] < TOKEN_LIMITS[model]

if __name__ == '__main__':
    make_prompt()
    #while make_prompt():
    #    pass