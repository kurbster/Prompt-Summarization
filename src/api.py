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
    probs = [os.path.basename(p) for p in probs]

    prompt, output_dir = select_summary_prompt(probs)

    # TODO: Get the problem category
    prompt_type = detect_type(prompt)
    
    # This is the prompt we want to summarize
    prompt, remainder = split_question(prompt)

    prompt_cfg = OmegaConf.load(cfg.promptFile)
    
    priming_prompts = [cfg.header]
    #priming_prompts.append(generate_example_prompt(prompt_type, prompt_cfg, probs))
    priming_prompts = priming_prompts + generate_example_prompt(prompt_type, prompt_cfg, probs)
    final_prompt = '\n\n'.join(priming_prompts) + f'\n\nJargon: {prompt}\nSimple:'
    # We must return the remainder to append it to the output file
    return final_prompt, remainder

def generate_example_prompt(prompt_type: str, prompt_cfg: OmegaConf, probs: list[str]) -> str:
    output = []
    # If it's a general problem choose any examples
    if prompt_type == 'general':
        example_prompts = random.sample(probs, cfg.numPrompts)

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
    prob = '4999'
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
    return prompt[:prompt_idx], prompt[prompt_idx:]
    
if __name__ == '__main__':
    cfg = OmegaConf.load('config.yaml')

    header = {'Authorization': f'Bearer {cfg.token}'}

    model = cfg.model
    url = f'https://api.ai21.com/studio/v1/j1-{model}/complete'

    prompt, extra = get_prompt(cfg)
    #print(prompt)
    prompt_dict = {'prompt': prompt}
    print(cfg)
    cfg = OmegaConf.merge(cfg.apiParams, prompt_dict)
    cfg = OmegaConf.to_container(cfg)
    data = {**cfg}

    #result = requests.post(url, headers=header, json=data)
    #text = result.json()['completions'][0]['data']['text']
    #json.dump(result.json(), open('output.json', 'w'), indent=4)
