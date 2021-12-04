#!/usr/bin/env python3
import re
import os
import sys
import json
import yaml
import glob
import shutil
import random
import logging

from pathlib import Path

logger = logging.getLogger('apiLogger')

path_to_src = Path(__file__, '../..').resolve()
path_to_data = path_to_src.joinpath('../data').resolve()

def find_path_to_cfg(func):
    def wrapper(*a, **kw):
        config = kw.pop('config', None)
        # If config was not specified in kwargs
        if config is None:
            # Then it must be declared in args
            if len(a) == 0:
                logger.critical('YOU NEED TO PASS THE NAME OF THE CONFIG FILE!!!')
                raise Exception('You must pass the name of the config to a function with this decerator.')
            else:
                config = a[-1]
                a = a[:-1]
        path_to_cfg_file = path_to_src.joinpath('configs', config)
        return func(*a, config=path_to_cfg_file, **kw)
    return wrapper

@find_path_to_cfg
def generate_code_prompt(config: str) -> tuple[list[str], list[str]]:
    """This will generate code generation prompts according to the config file passed in.

    Args:
        config (str): The yaml file holding the generation config.

    Returns:
        tuple[list[str], list[str]]: The first is the list of prompt strings to pass to the model.
        The second is the output dir for each problem.
    """
    with open(config) as f:
        cfg = yaml.safe_load(f)

    prompts, num_remaining = validate_prompts(cfg, cfg['promptFile'])

    human_probs, model_probs = get_completed_problems()
    available_prompts = human_probs if cfg['humanOnly'] else human_probs | model_probs
    
    # These are the prompt we want to summarize
    prompts = select_code_prompts(prompts, num_remaining, available_prompts, cfg)

    # If we include original we return a new set of prompts
    prompt_texts, prompts = generate_example_code(prompts, available_prompts, cfg)

    return prompt_texts, prompts

@find_path_to_cfg
def generate_summary_prompt(api: str, config: str) -> tuple[str, str, str]:
    """This will generate a prompt for summarization based on the
    configuration file passed in.

    Args:
        api (str): The api calling this function.
        cfg (str): The name of the config file to use.

    Returns:
        tuple[str, str, str]: The full prompt, the remaining section to be
        added to the output, and the path to the output directory.
    """
    with open(config) as f:
        cfg = yaml.safe_load(f)

    human_probs, model_probs = get_completed_problems(api=api)

    # Select a summary prompt that hasn't been summarized
    ignore_intro = cfg.get('ignoreIntro', True)
    ignore_train  = cfg.get('ignoreTrain', True) 
    original_prompt_fname = select_summary_prompt(
                    human_probs | model_probs,
                    ignore_intro=ignore_intro,
                    ignore_train=ignore_train)

    output_dir = save_config(original_prompt_fname, config, f'data/{api}_generated', cfg['promptFile'])

    prompt_type = detect_type(original_prompt_fname)

    prompt, remainder = split_prompt(original_prompt_fname, cfg['splitFile'])

    priming_examples = generate_example_prompt(prompt_type, cfg, human_probs, cfg['promptFile'])

    full_example = priming_examples + f'{cfg["fewShotSuffix"]}{cfg["originalPrefix"]}{prompt}\n{cfg["summaryPrefix"]}'

    # Remove ending whitespace to increase accuracy
    full_example = remove_ending_whitespace(full_example)

    full_example = ensure_ascii(full_example)
    
    return full_example, remainder, output_dir

def get_completed_problems(api: str = '*') -> tuple[set[str], set[str]]:
    """Get the problems that have already been summarized.

    Args:
        api (str, optional): Allows us to select specific model probs. 
        Defaults to '*' which gets all model generated problems.
    
    Returns:
        tuple(set[str], set[str]): The first set is the problems that
        a human has summarized. The second set is the problems that a
        model has summarized.
    """
    human_probs = set(glob.glob(f'{path_to_data}/[ic]*/*'))
    train_probs = set(glob.glob(f'{path_to_data}/{api}_generated/[ic]*/*'))
    test_probs  = set(glob.glob(f'{path_to_data}/{api}_generated/test/[ic]*/*'))

    model_probs = train_probs | test_probs

    logger.debug(f'Found {len(human_probs)} human generated summaries.')
    logger.debug(f'Found {len(model_probs)} model generated summaries.')

    return human_probs, model_probs
    
def select_summary_prompt(probs: set[str], ignore_intro: bool = True, ignore_train: bool = True) -> str:
    """Select a random problem to be summarized by the model.

    Args:
        probs (set[str]): A set of problems we have already done.
        ignore_intro (bool, optional): If you want to avoid summarizing
        introductory problems. Defaults to True.
        ignore_train (bool, optional): If you want to avoid summarizing
        problems from the training set. Defaults to True.

    Returns:
        str: The path to the question we are summarizing.
    """
    # introductory problems in the train set are from 2361 - 4999. 
    # In the test set are 4000 - 4999, which count as 9000 - 9999.
    available_probs = set(range(10000))

    if ignore_intro:
        available_probs -= set(range(9000, 10000))
        available_probs -= set(range(2361, 5000))
        logger.info('Ignoring introductory problems.')
    if ignore_train:
        available_probs -= set(range(5000))
        logger.info('Ignoring training problems.')

    # This is limiting the number of examples we will generate with GPT.
    # There are 250 competitive and 250 interview available.
    available_probs -= set(range(8000, 8761))
    available_probs -= set(range(5000, 7785))

    def get_num(x):
        num = int(os.path.basename(x))
        if 'test' in x:
            num += 5000
        return num

    probs = set(map(get_num, probs))
    available_probs -= probs

    logger.debug(f'There are {len(available_probs)} remaining problems to summarize.')
    if len(available_probs) == 0:
        raise BaseException("There are no more problems!")
    available_probs = list(available_probs)
    prob_to_summarize = random.choice(available_probs)

    path_to_apps = path_to_src.joinpath('../APPS').resolve()

    if prob_to_summarize >= 5000:
        prob_to_summarize -= 5000
        fname = f'{path_to_apps}/test/*/{str(prob_to_summarize).zfill(4)}/question.txt'
    else:
        fname = f'{path_to_apps}/*/{str(prob_to_summarize).zfill(4)}/question.txt'

    original_prompt = glob.glob(fname)[0]

    return original_prompt

@find_path_to_cfg
def save_config(prompt_fname: str, cfg_fname: str, output_path: str, config: str) -> str:
    """We will copy the original files and config used for this generation.

    Args:
        prompt_fname (str): Name of the file we are summarizing.
        cfg_fname (str): Name of the config file.
        output_path (str): Prefix of the path to save to.
        config (str): Name of the prompt categories config file.

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
    shutil.copy(config, output_dir)

    return output_dir

def detect_type(fname: str) -> str:
    logger.info(f'Summarizing the file: {fname}')
    return 'general'

@find_path_to_cfg
def split_prompt(fname: str, config: str) -> tuple[str, str]:
    """This will split the original prompt into the question and
    the information section.

    Args:
        fname (str): The file we want to split.
        config (str): The file that defines the different splits.

    Returns:
        tuple(str, str): The question and the information section.
    """
    with open(fname) as f:
        prompt = f.read().splitlines()

    with open(config) as f:
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

@find_path_to_cfg
def generate_example_prompt(prompt_type: str, cfg: dict[str, any], probs: set[int], config: str) -> str:
    """Generating the examples that will be passed to the model before the new summary.

    Args:
        prompt_type (str): The determined type of the problem.
        cfg (dict[str, any]): The configuration for this generation.
        probs (set[int]): The human problems to choose from.
        config (str): The prompt category config file.

    Returns:
        str: The formatted examples for this generation.
    """
    # TODO: Implement the problem categories
    with open(config) as f:
        prompt_cfg = yaml.safe_load(f)
    
    output = []
    if cfg['header']:
        output = [cfg['header']]
    
    probs = list(probs)
    # If it's a general problem choose any examples
    if prompt_type == 'general':
        example_prompts = random.sample(probs, cfg['numPrompts'])

    for ex in example_prompts:
        # Get the original prompt and the summarized
        orig = os.path.join(ex, 'question.txt')
        summary = os.path.join(ex, f'{cfg["summaryType"]}.txt')
        logger.debug(f'Using summary {summary} for priming model')
        orig, _ = split_prompt(orig, cfg['splitFile'])
        summary, _ = split_prompt(summary, cfg['splitFile'])
        output.append(f'{cfg["originalPrefix"]}{orig}\n{cfg["summaryPrefix"]}{summary}')
    
    for text, num in zip(output, example_prompts):
        if not check_ascii(text):
            logger.warning(f'Problem {num} was not ascii.')

    output = cfg["fewShotSuffix"].join(output)
    
    return output

def remove_ending_whitespace(prompt: str) -> str:
    """Remove ending whitespace from string.

    Args:
        prompt (str): prompt to remove from

    Returns:
        str: The resulting string
    """
    return prompt.rstrip()

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

@find_path_to_cfg
def validate_prompts(cfg: dict[str, any], config: str) -> tuple[set[str], int]:
    """Read the specified prompts and determine how many more we need to choose.

    Args:
        cfg (dict[str, any]): The configuration dict.
        config (str): The path to the prompt config file, that is
        specified in the codex config file.

    Returns:
        tuple[set[str], int]: The set of paths to the problems we want to generate for,
        and the number of remaining prompts we have to choose.
    """
    prompts = {}
    num_prompts = cfg['numPrompts']
    
    # Read the lines from the prompt file
    with open(config) as f:
        prompts = f.read().splitlines()

    add_data_dir = lambda x: os.path.join(path_to_data, x)

    prompts = set(map(add_data_dir, prompts))
    remaining_prompts = num_prompts - len(prompts)

    # We provide every example to use
    if num_prompts == -1 or remaining_prompts == 0:
        logger.info(f'Only using prompts specified in {cfg["promptFile"]}')
        return prompts, 0

    # We provided too many examples
    if remaining_prompts < 0:
        err_str = f'You provided {len(prompts)} prompts in the promptFile.'
        err_str += f'But only specified {cfg["numPrompts"]} in your config file. Exiting.'
        logger.critical(err_str)
        sys.exit(1)

    return prompts, remaining_prompts

def select_code_prompts(prompts: set[str], num_remaining: int, available_prompts: set[str], cfg: dict[str, any]) -> set[str]:
    """Select prompts to generate code for.

    Args:
        prompts (set[str]): Prompts already selected.
        num_remaining (int): Number of prompts to select.
        available_prompts (set[str]): Completed problems to choose from.
        cfg (dict[str, any]): Our configuration dictionary.

    Returns:
        set[str]: The problems to generate code for.
    """
    if num_remaining:
        # Only select from prompts not already chosen
        remaining_prompts = available_prompts - prompts
        logger.debug(f'Choosing {num_remaining} prompts from {len(remaining_prompts)} remaining prompts.')
        extra_prompts = set(random.sample(remaining_prompts, num_remaining))
        prompts |= extra_prompts

    return prompts

def generate_example_code(prompts: set[str], available_prompts: set[str], cfg: dict[str, any]) -> tuple[list[str], list[str]]:
    """Generate the prompt to pass to the API from the prompts selected.

    Args:
        prompts (set[str]): The filenames of the prompts to generate code for.
        available_prompts (set[str]): The prompts available to select for few shot.
        cfg (dict[str, any]): The configuration dict.

    Returns:
        tuple[list[str], list[str]]: The list of string prompts to be passed to the model.
        The list of prompts used to generate the strings.
    """
    code_prompts = []
    prompt_paths = []
    for prompt in prompts:
        logger.info(f'Generating code for prompt: {prompt}')

        # Remove current prob from few shot pool
        # TODO: Should we remove from the available prompts if we are using that prompt?
        # currenty we do not.
        few_shot_list = generate_few_shot(available_prompts - {prompt}, cfg)
        few_shot_str = cfg['fewShotSuffix'].join(few_shot_list)

        summary = read_code_files(prompt, cfg, read_solution=False)

        prompt_str = cfg['header'] + few_shot_str + summary
        prompt_str = remove_ending_whitespace(prompt_str)
        code_prompts.append(prompt_str)
        
        prompt_name = os.path.join(prompt, cfg['summaryType']+'.txt')
        prompt_paths.append(prompt_name)

        if cfg['includeOrig']:
            logger.info(f'Generating code with original prompt for problem: {prompt}')
            original = read_code_files(prompt, cfg, read_original=True, read_solution=False)
            
            prompt_str = cfg['header'] + few_shot_str + original
            prompt_str = remove_ending_whitespace(prompt_str)
            code_prompts.append(prompt_str)
            
            prompt_name = os.path.join(prompt, 'question.txt')
            prompt_paths.append(prompt_name)
    
    return code_prompts, prompt_paths

def generate_few_shot(available_prompts: set[str], cfg: dict[str, any]) -> list[str]:
    """Generating few shot examples.

    Args:
        available_prompts (set[str]): Set of prompts to choose from.
        cfg (dict[str, any]): The configuration dict.

    Returns:
        list[str]: The list of few shot prompts.
    """
    if cfg['numExamples'] == 0:
        return []
    
    available_prompts = list(available_prompts)
    few_shot_examples = random.sample(available_prompts, cfg["numExamples"])
    
    # TODO: Currently we generate few shot examples by reading the summaries.
    # The summary type is defined in the config file. Should we change this
    # to have different few shot examples if we are using the original question?
    examples = [read_code_files(ex, cfg) for ex in few_shot_examples]
    
    return examples

def read_code_files(prompt: str, cfg: dict[str, any], read_original: bool=False, read_solution: bool=True) -> str:
    """Read the appropriate files from the prompt dir and format into string.

    Args:
        prompt (str): The directory to read from.
        cfg (dict[str, any]): The configuration dict.
        read_original (bool, optional): Whether or not to read the orginal question. Defaults to False.
        read_solution (bool, optional): Whether or not to read solutions.json. Defaults to True.

    Returns:
        str: The str to be passed as input.
    """
    fname = 'question.txt' if read_original else f'{cfg["summaryType"]}.txt'
    question_fname = os.path.join(prompt, fname)
    logger.info(f'Generating prompt for file: {question_fname}')
    with open(question_fname) as f:
        question = f.read()

    code_prefix = get_code_prefix(prompt, cfg["codePrefix"])

    prompt_str  = f'{cfg["promptPrefix"]}\n{question}\n{cfg["promptSuffix"]}\n{code_prefix}'
    
    if read_solution:
        code_fname = os.path.join(prompt, 'solutions.json')
        try:
            code = json.load(open(code_fname))[0]   
            prompt_str += '\n' + code
        except FileNotFoundError:
            logger.error(f'The code solution for prompt {prompt} does not exist. Not including it in few shot examples.')
        
    return prompt_str

def get_code_prefix(prompt: str, default: str) -> str:
    """Return the prefix for code generation.

    Args:
        prompt (str): The problem directory to read from.
        default (str): The default prefix to use if the starter code doesn't exist.

    Returns:
        str: The code prefix used for code generation.
    """
    starter_code = os.path.join(prompt, 'starter_code.py')
    prefix = default
    if os.path.exists(starter_code):
        with open(starter_code) as f:
            prefix = f.read().strip()
    else:
        logger.warning(f'The problem {prompt} did not have starter_code.py!')
    return prefix

def log_summary(prompt, extra, output_dir):
    logger.debug(f'PROMPT:\n{prompt}')
    logger.debug(f'EXTRA:\n{extra}')
    logger.debug(f'OUTPUT DIR: {output_dir}')

def log_codes(prompts, output_dirs):
    for p, out in zip(prompts, output_dirs):
        logger.debug(f'Prompt for output {out}')
        logger.debug('='*50)
        logger.debug(p)

if __name__ == '__main__':
    import my_logger
    prompt, extra, output_dir = generate_summary_prompt('studio21', config='studio21_config.yaml')
    logger.info('BEGIN STUDIO21 TEST')
    log_summary(prompt, extra, output_dir)
    logger.info('END STUDIO21 TEST')

    prompt, extra, output_dir = generate_summary_prompt('gpt', 'gpt_config.yaml')
    logger.info('BEGIN GPT TEST')
    log_summary(prompt, extra, output_dir)
    logger.info('END GPT TEST')

    prompts, output_dirs = generate_code_prompt('codex_config.yaml')
    logger.info('BEGIN CODEX TEST')
    log_codes(prompts, output_dirs)
    logger.info('END CODEX TEST')
    logger.info('Test results logged as level DEBUG. Look in latest log file. \
Or use level DEBUG for the console logger.')
else:
    from . import my_logger