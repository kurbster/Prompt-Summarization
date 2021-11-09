#!/usr/bin/env python3
import re
import os
import yaml
import glob
import shutil
import random
import logging
import logging.config

from datetime import datetime

with open('logging.yaml') as f:
    cfg = yaml.safe_load(f)

fname = 'logs/' + datetime.now().strftime('%m-%d-%Y_%H:%M:%S') + '.log'
cfg['handlers']['file']['filename'] = fname
logging.config.dictConfig(cfg)
logger = logging.getLogger('apiLogger')

def generate_prompt(config: str = 'config.yaml') -> tuple[str, str, str]:
    """This will generate a prompt for summarization based on the
    configuration file passed in.

    Args:
        cfg (str, optional): The name of the config file to use.
        Defaults to 'config.yaml'.

    Returns:
        tuple[str, str, str]: The full prompt, the remaining section to be
        added to the output, and the path to the output directory.
    """
    with open(config) as f:
        cfg = yaml.safe_load(f)

    human_probs, model_probs = get_completed_problems()

    # Select a summary prompt that hasn't been summarized
    original_prompt_fname = select_summary_prompt(
                    human_probs+model_probs, ignore_intro=cfg['ignoreIntro'])

    output_dir = save_config(original_prompt_fname, config, cfg['promptFile'])

    prompt_type = detect_type(original_prompt_fname)

    prompt, remainder = split_prompt(original_prompt_fname, cfg['splitFile'])

    priming_examples = generate_example_prompt(prompt_type, cfg, human_probs)

    full_example = priming_examples + f'\n\n{cfg["originalPrefix"]} {prompt}\n{cfg["summaryPrefix"]}'

    full_example = ensure_ascii(full_example)
    
    return full_example, remainder, output_dir
    
def get_completed_problems() -> tuple[list[int], list[int]]:
    """Get the problems that have already been summarized.

    Returns:
        tuple(list[int], list[int]): The first list is the problems that
        a human has summarized. The second list is the problems that a
        model has summarized.
    """
    human_probs = glob.glob('../data/[ic]*/*')
    train_probs = glob.glob('../data/studio21_generated/[ic]*/*')
    test_probs  = glob.glob('../data/studio21_generated/test/[ic]*/*')

    get_num = lambda x: int(os.path.basename(x))

    human_probs = list(map(get_num, human_probs))
    train_probs = list(map(get_num, train_probs))
    test_probs  = list(map(get_num, test_probs))
    
    test_probs = list(map(lambda x: x + 5000, test_probs))

    model_probs = train_probs + test_probs

    logger.debug(f'Found {len(human_probs)} human generated summaries.')
    logger.debug(f'Found {len(model_probs)} model generated summaries.')

    return human_probs, model_probs
    
def select_summary_prompt(probs: list[int], ignore_intro: bool = True) -> str:
    """Select a random problem to be summarized by the model.

    Args:
        probs (list[int]): A list of problems we have already done.
        ignore_intro (bool, optional): If you want to avoid summarizing
        introductory problems. Defaults to True.

    Returns:
        str: The path to the question we are summarizing.
    """
    # introductory problems in the train set are from 2361 - 4999. 
    # In the test set are 4000 - 4999, which count as 9000 - 9999.
    intro_probs = []
    if ignore_intro:
        intro_probs = list(range(2361, 5000)) + list(range(9000, 10000))
        logger.info('Ignoring introductory problems.')

    completed_probs = set(probs + intro_probs)
    
    available_probs = [i for i in range(10000) if i not in completed_probs]

    logger.debug(f'There are {len(available_probs)} remaining problems to summarize.')
    assert len(available_probs) + len(completed_probs) == 10000, f'The total probs must add to 10000. It is {len(available_probs) + len(completed_probs)}'

    prob_to_summarize = random.choice(available_probs)

    if prob_to_summarize >= 5000:
        prob_to_summarize -= 5000
        fname = f'../APPS/test/*/{str(prob_to_summarize).zfill(4)}/question.txt'
    else:
        fname = f'../APPS/*/{str(prob_to_summarize).zfill(4)}/question.txt'

    original_prompt = glob.glob(fname)[0]

    return original_prompt

def save_config(prompt_fname: str, cfg_fname: str, prompt_cfg_fname: str) -> str:
    """We will copy the original files and config used for this generation.

    Args:
        prompt_fname (str): Name of the file we are summarizing.
        cfg_fname (str): Name of the config file.
        prompt_cfg_fname (str): Name of the prompt categories config file.

    Returns:
        str: The path to where the example was saved.
    """
    # Copy the original directory to the output directory
    prompt_dir = os.path.split(prompt_fname)[0]
    output_dir = prompt_dir.replace('APPS', 'data/studio21_generated')
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

def generate_example_prompt(prompt_type: str, cfg: dict[str, any], probs: list[int]) -> str:
    """Generating the examples that will be passed to the model before the new summary.

    Args:
        prompt_type (str): The determined type of the problem.
        cfg (dict[str, any]): The configuration for this generation.
        probs (list[int]): The human problems to choose from.

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

if __name__ == '__main__':
    prompt, extra, output_dir = generate_prompt()
    print(prompt)
    print(extra)
    print(output_dir)
