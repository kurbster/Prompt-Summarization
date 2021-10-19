#!/usr/bin/env python3
import os
import json
import glob
import random
import requests

from omegaconf import OmegaConf

def get_prompt(cfg: OmegaConf) -> str:
    # Get the problems we have already done
    probs = glob.glob('../[ic]*/*')
    probs = [os.path.basename(p) for p in probs]

    # Select a random problem
    total_probs = [str(i).zfill(4) for i in range(5000) if str(i).zfill(4) not in probs]
    assert len(total_probs) + len(probs) == 5000, f'The total probs must add to 5000'
    prob = random.choice(total_probs)
    prompt = glob.glob(f'../APPS/*/{prob}/question.txt')

    # TODO: Get the problem category
    prompt_type = detect_type(prompt)

    # This is the prompt we want to summarize
    prompt, remainder = split_question(prompt[0])
    
    prompt_cfg = OmegaConf.load(cfg.promptFile)
    # If it's a general problem choose any examples
    if prompt_type == 'general':
        example_prompts = random.sample(probs, cfg.numPrompts)
        

    priming_prompts = [cfg.header]
    for ex in example_prompts:
        # Get the original prompt and the summarized
        orig = glob.glob(f'../[ic]*/{ex}/question.txt')
        example = glob.glob(f'../[ic]*/{ex}/{cfg.summaryType}.txt')
        print(f'Using summary {example} for priming model')
        orig, _ = split_question(orig[0])
        example, _ = split_question(example[0])
        priming_prompts.append(f'Jargon: {orig}\nSimple: {example}')

    final_prompt = '\n\n'.join(priming_prompts) + f'\n\nJargon: {prompt}\nSimple:'
    # We must return the remainder to append it to the output file
    return final_prompt, remainder

def detect_type(fname: str) -> str:
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

    result = requests.post(url, headers=header, json=data)
    test = result.json()['completions'][0]['data']['text']
    print(test)
    json.dump(result.json(), open('output.json', 'w'), indent=4)
