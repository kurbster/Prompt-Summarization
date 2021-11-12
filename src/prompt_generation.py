#!/usr/bin/env python3
import re
import os
import sys
import yaml
import glob
import shutil
import random
import logging

import my_logger

logger = logging.getLogger('apiLogger')

def generate_code_prompt(config: str = 'config.yaml') -> tuple[str, str]:
    with open(config) as f:
        cfg = yaml.safe_load(f)

    prompts, num_remaining = validate_prompts(cfg)

    # These are the prompt we want to summarize
    prompts = select_code_prompts(prompts, num_remaining, cfg)

    generate_example_code(prompts, cfg)

    return 'Hello World'

def generate_prompt(api: str, config: str = 'config.yaml') -> tuple[str, str, str]:
    """This will generate a prompt for summarization based on the
    configuration file passed in.

    Args:
        api (str): The api calling this function.
        cfg (str, optional): The name of the config file to use.
        Defaults to 'config.yaml'.

    Returns:
        tuple[str, str, str]: The full prompt, the remaining section to be
        added to the output, and the path to the output directory.
    """
    with open(config) as f:
        cfg = yaml.safe_load(f)

    human_probs, model_probs = get_completed_problems(cfg['pathToData'])

    # Select a summary prompt that hasn't been summarized
    original_prompt_fname = select_summary_prompt(
                    human_probs | model_probs, ignore_intro=cfg['ignoreIntro'])

    output_dir = save_config(original_prompt_fname, config, cfg['promptFile'], f'data/{api}_generated')

    prompt_type = detect_type(original_prompt_fname)

    prompt, remainder = split_prompt(original_prompt_fname, cfg['splitFile'])

    priming_examples = generate_example_prompt(prompt_type, cfg, human_probs)

    full_example = priming_examples + f'\n\n{cfg["originalPrefix"]} {prompt}\n{cfg["summaryPrefix"]}'

    full_example = ensure_ascii(full_example)
    
    return full_example, remainder, output_dir
    
def get_completed_problems(path_to_data: str) -> tuple[set[str], set[str]]:
    """Get the problems that have already been summarized.

    Args:
        path_to_data (str): Path to the data directory.

    Returns:
        tuple(set[str], set[str]): The first set is the problems that
        a human has summarized. The second set is the problems that a
        model has summarized.
    """
    human_probs = set(glob.glob(f'{path_to_data}/[ic]*/*'))
    train_probs = set(glob.glob(f'{path_to_data}/*generated/[ic]*/*'))
    test_probs  = set(glob.glob(f'{path_to_data}/*generated/test/[ic]*/*'))

    model_probs = train_probs | test_probs

    logger.debug(f'Found {len(human_probs)} human generated summaries.')
    logger.debug(f'Found {len(model_probs)} model generated summaries.')

    return human_probs, model_probs
    
def select_summary_prompt(probs: set[str], ignore_intro: bool = True) -> str:
    """Select a random problem to be summarized by the model.

    Args:
        probs (set[str]): A set of problems we have already done.
        ignore_intro (bool, optional): If you want to avoid summarizing
        introductory problems. Defaults to True.

    Returns:
        str: The path to the question we are summarizing.
    """
    # introductory problems in the train set are from 2361 - 4999. 
    # In the test set are 4000 - 4999, which count as 9000 - 9999.
    intro_probs = []
    available_probs = set(range(10000))

    if ignore_intro:
        available_probs -= set(range(2361, 5000))
        available_probs -= set(range(9000, 10000))
        logger.info('Ignoring introductory problems.')

    def get_num(x):
        num = int(os.path.basename(x))
        if 'test' in x:
            num += 5000
        return num

    probs = set(map(get_num, probs))
    available_probs -= probs

    logger.debug(f'There are {len(available_probs)} remaining problems to summarize.')

    available_probs = list(available_probs)
    prob_to_summarize = random.choice(available_probs)

    if prob_to_summarize >= 5000:
        prob_to_summarize -= 5000
        fname = f'../APPS/test/*/{str(prob_to_summarize).zfill(4)}/question.txt'
    else:
        fname = f'../APPS/*/{str(prob_to_summarize).zfill(4)}/question.txt'

    original_prompt = glob.glob(fname)[0]

    return original_prompt

def save_config(prompt_fname: str, cfg_fname: str, prompt_cfg_fname: str, output_path: str) -> str:
    """We will copy the original files and config used for this generation.

    Args:
        prompt_fname (str): Name of the file we are summarizing.
        cfg_fname (str): Name of the config file.
        prompt_cfg_fname (str): Name of the prompt categories config file.
        output_path (str): Prefix of the path to save to.

    Returns:
        str: The path to where the example was saved.
    """
    # Copy the original directory to the output directory
    prompt_dir = os.path.split(prompt_fname)[0]
    output_dir = prompt_dir.replace('APPS', output_path)
    shutil.copytree(prompt_dir, output_dir)

    logger.debug(f'Saved original prompt directory to {output_dir}')

    # Save config files in output dir
    shutil.copy(cfg_fname, output_dir)
    shutil.copy(prompt_cfg_fname, output_dir)

    return output_dir

def detect_type(fname: str) -> str:
    logger.info(f'Summarizing the file: {fname}')
    return 'general'

def split_prompt(fname: str, split_file: str) -> tuple[str, str]:
    """This will split the original prompt into the question and
    the information section.

    Args:
        fname (str): The file we want to split.
        split_file (str): The file that defines the different splits.

    Returns:
        tuple(str, str): The question and the information section.
    """
    with open(fname) as f:
        prompt = f.read().splitlines()

    with open(split_file) as f:
        re_str = f.read().splitlines()

    re_str = '|'.join(re_str)
    regex = re.compile(re_str)

    # Only join non empty lines
    prompt = [t for t in prompt if t]
    prompt = ' '.join(prompt)

    # Find the information section
    prompt_idx = -1
    match = regex.search(prompt)
    if match:
        prompt_idx = match.span()[0]
    else:
        logger.error(f'A split was not found for file {fname}')

    return prompt[:prompt_idx], prompt[prompt_idx:]

def generate_example_prompt(prompt_type: str, cfg: dict[str, any], probs: set[int]) -> str:
    """Generating the examples that will be passed to the model before the new summary.

    Args:
        prompt_type (str): The determined type of the problem.
        cfg (dict[str, any]): The configuration for this generation.
        probs (set[int]): The human problems to choose from.

    Returns:
        str: The formatted examples for this generation.
    """
    # TODO: Implement the problem categories
    with open(cfg['promptFile']) as f:
        prompt_cfg = yaml.safe_load(f)
    
    output = [cfg['header']]
    
    # If it's a general problem choose any examples
    if prompt_type == 'general':
        example_prompts = random.sample(probs, cfg['numPrompts'])

    for ex in example_prompts:
        ex = str(ex).zfill(4)
        # Get the original prompt and the summarized
        orig = glob.glob(f'../data/[ic]*/{ex}/question.txt')[0]
        summary = glob.glob(f'../data/[ic]*/{ex}/{cfg["summaryType"]}.txt')[0]
        logger.debug(f'Using summary {summary} for priming model')
        orig, _ = split_prompt(orig, cfg['splitFile'])
        summary, _ = split_prompt(summary, cfg['splitFile'])
        output.append(f'{cfg["originalPrefix"]} {orig}\n{cfg["summaryPrefix"]} {summary}')
    
    for text, num in zip(output, example_prompts):
        if not check_ascii(text):
            logger.warning(f'Problem {num} was not ascii.')

    output = '\n\n'.join(output)
    
    return output

def ensure_ascii(text: str) -> str:
    """Convert the text into ASCII.

    Args:
        text (str): The text to convert.

    Returns:
        str: The converted text.
    """
    # TODO: Should we use python's ascii method?
    # That method will escape any non ascii character and
    # potentially confuse the model and increase token count.
    text = text.encode('ascii', 'replace')
    text = text.decode('ascii')
    text = text.replace('?', ' ')
    if not check_ascii(text):
        logger.error(f'THE FINAL PROMPT IS NOT ASCII!!!')

    return text

def check_ascii(text: str) -> bool:
    """Check is a string is ASCII.

    Args:
        text (str): The string to check.

    Returns:
        bool: False means the text was not ASCII.
    """
    if any(ord(c) >= 128 for c in text):
        return False
    return True

def validate_prompts(cfg: dict[str, any]) -> tuple[set[str], int]:
    prompts = {}
    num_prompts = cfg['numPrompts']
    if 'promptFile' not in cfg:
        return prompts, num_prompts
    
    # Read the lines from the prompt file
    with open(cfg['promptFile']) as f:
        prompts = f.read().splitlines()

    add_data_dir = lambda x: os.path.join(cfg['pathToData'], x)

    prompts = set(map(add_data_dir, prompts))
    remaining_prompts = num_prompts - len(prompts)

    # We provide every example to use
    if num_prompts == -1 or remaining_prompts == 0:
        return prompts, 0

    # We provided too many examples
    if remaining_prompts < 0:
        err_str = f'You provided {len(prompts)} prompts in the promptFile.'
        err_str += f'But only specified {cfg["numPrompts"]} in your config file. Exiting.'
        logger.critical(err_str)
        sys.exit(1)

    return prompts, remaining_prompts

def select_code_prompts(prompts: set[str], num_remaining: int, cfg: dict[str, any]) -> set[str]:
    """Select prompts to generate code for.

    Args:
        prompts (set[str]): Prompts already selected.
        num_remaining (int): Number of prompts to select.
        cfg (dict[str, any]): Our configuration dictionary.

    Returns:
        set[str]: The problems to generate code for.
    """
    if num_remaining:
        human_probs, model_probs = get_completed_problems(cfg['pathToData'])
        probs = human_probs if cfg['humanOnly'] else human_probs | model_probs

        # Only select from prompts not already chosen
        remaining_prompts = probs - prompts
        extra_prompts = set(random.sample(remaining_prompts, num_remaining))
        prompts |= extra_prompts
    return prompts

def generate_example_code(prompts: set[str], cfg: dict[str, any]) -> str:
    """Generate the prompt to pass to the API from the prompts selected.

    Args:
        prompts (set[str]): The filenames of the prompts to generate code for.
        cfg (dict[str, any]): The configuration dict.

    Returns:
        str: The string to pass to a model.
    """
    codes = []
    for prompt in prompts:
        prompt_str = ''
        prompt_type = cfg['summaryType'] + '.txt'
        prompt_file = os.path.join(prompt, prompt_type)
        logging.info(f'Generating code for file: {prompt_file}')
        #codes.append(prompt_str)

def add_few_shot(prompt: str, num_shots: int) -> str:
    pass

if __name__ == '__main__':
    prompt, extra, output_dir = generate_prompt('studio21')
    print(prompt)
    print(extra)
    print(output_dir)
