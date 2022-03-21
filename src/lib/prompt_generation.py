#!/usr/bin/env python3
import re
import os
import sys
import json
import yaml
import glob
import hydra
import shutil
import random
import logging

from omegaconf import OmegaConf
from typing import List, Tuple, Set
from pathlib import Path

try:
    from config import CodexConfig, GenerationConfig, ExperimentConfig, register_configs
except ImportError:
    from .config import CodexConfig, GenerationConfig, ExperimentConfig, register_configs

logger = logging.getLogger('apiLogger')

PATH_TO_SRC = Path(__file__, '../..').resolve()
PATH_TO_DATA = PATH_TO_SRC.joinpath('../data').resolve()
PATH_TO_MANIFESTS = PATH_TO_SRC.joinpath('configs/manifests')

def generate_code_prompt(cfg: CodexConfig) -> tuple[list[str], list[str]]:
    """This will generate code generation prompts according to the config file passed in.

    Args:
        config (GenerationConfig): The config object

    Returns:
        tuple[list[str], list[str]]: The first is the list of prompt strings to pass to the model.
        The second is the output dir for each problem.
    """
    prompts, num_remaining = validate_prompts(cfg)

    human_probs, model_probs = get_completed_problems()
    available_prompts = human_probs if cfg.human_only else human_probs | model_probs
    
    # These are the prompt we want to summarize
    prompts = select_code_prompts(prompts, num_remaining, available_prompts)

    # If we include original we return a new set of prompts
    prompt_texts, prompts = generate_example_code(prompts, available_prompts, cfg)

    logger.info(f'Generated a total of {len(prompt_texts)} examples')
    return prompt_texts, prompts

def generate_summary_prompt(cfg: GenerationConfig) -> Tuple[List[str], List[str], List[str]]:
    """This will generate a prompt for summarization based on the
    configuration file passed in.

    Args:
        cfg (GenerationConfig): Our config object

    Returns:
        Tuple[List[str], List[str], List[str]]: The full prompt, the remaining section to be
        added to the output, and the path to the output directory.
    """
    prompts, num_remaining = validate_prompts(cfg)

    prompts = convert_to_apps_format(prompts)

    human_probs, model_probs = get_completed_problems(cfg.api_name)

    # Select a summary prompt that hasn't been summarized
    original_prompt_fnames = select_summary_prompt(
                    prompts,
                    human_probs | model_probs,
                    num_remaining,
                    ignore_intro=cfg.ignore_intro,
                    ignore_train=cfg.ignore_train)

    prompt_types = [detect_type(fname) for fname in original_prompt_fnames]

    prompts, remainders = split_prompts(original_prompt_fnames, cfg)

    full_prompts = generate_prompts(prompts, prompt_types, human_probs, cfg)

    # If successful copy over to data dir and save config
    output_dirs = [
        save_config(fname, cfg, f'data/{cfg.api_name}_generated')
        for fname in original_prompt_fnames
    ]

    logger.info(f'Generated a total of {len(full_prompts)} examples')
    return full_prompts, remainders, output_dirs

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
    regex_for_problem_dirs = '*/[ic]*/*'
    human_probs = set(glob.glob(f'{PATH_TO_DATA}/human_generated/{regex_for_problem_dirs}'))
    model_probs = set(glob.glob(f'{PATH_TO_DATA}/{api}_generated/{regex_for_problem_dirs}'))

    logger.debug(f'Found {len(human_probs)} human generated summaries.')
    logger.debug(f'Found {len(model_probs)} model generated summaries.')

    return human_probs, model_probs
    
def select_summary_prompt(
    prompts: Set[str],
    completed_prompts: Set[str],
    num_remaining: int,
    ignore_intro: bool = True,
    ignore_train: bool = True) -> List[str]:
    """Select prompts to generate summaries for.

    Args:
        prompts (Set[str]): Set of prompts already specified in config.
        completed_prompts (Set[str]): Set of prompts already summarized.
        num_remaining (int): Number of prompts left to pick.
        ignore_intro (bool, optional): If true we ignore introductory problems
        when selecting prompts. Defaults to True.
        ignore_train (bool, optional): If true we ignore training problems
        when selecting prompts. Defaults to True.

    Returns:
        Set[str]: A list of paths to each prompt to summarize.
    """
    if not num_remaining:
        return prompts
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

    def get_num(x):
        num = int(os.path.basename(x))
        if 'test' in x:
            num += 5000
        return num

    completed_nums = set(map(get_num, completed_prompts))
    available_probs -= completed_nums

    logger.debug(f'Choosing {num_remaining} from {len(available_probs)} remaining problems.')
    if len(available_probs) == 0:
        logger.critical('There are no more problems to summarize.')
        sys.exit()
    available_probs = list(available_probs)
    probs_to_summarize = random.sample(available_probs, num_remaining)

    path_to_apps = PATH_TO_SRC.joinpath('../APPS').resolve()

    def find_problem(num: int) -> str:
        if num >= 5000:
            num -= 5000
            fname = f'{path_to_apps}/test/*/{str(num).zfill(4)}/question.txt'
        else:
            fname = f'{path_to_apps}/train/*/{str(num).zfill(4)}/question.txt'

        return glob.glob(fname)[0]
    
    paths_to_summarize = set(map(find_problem, probs_to_summarize))

    logger.debug(f'Selected {len(paths_to_summarize)} prompts randomly.')

    return prompts | paths_to_summarize

def save_config(prompt_fname: str, cfg: GenerationConfig, output_path: str) -> str:
    """We will copy the original files and config used for this generation.

    Args:
        prompt_fname (str): Name of the file we are summarizing.
        cfg (GenerationConfig): Our config object.
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
    with open(output_dir+'/config.yaml', 'w') as f:
        f.write(OmegaConf.to_yaml(cfg))

    category_path = PATH_TO_MANIFESTS.joinpath(cfg.category_file)
    shutil.copy(category_path, output_dir)

    return output_dir

# TODO: Have this function detect what type of problem we are summarizing.
# i.e strings, graph, arrays, etc.
def detect_type(fname: str) -> str:
    logger.info(f'Summarizing the file: {fname}')
    return 'general'

def split_prompts(fnames: Set[str], config: GenerationConfig) -> Tuple[List[str], List[str]]:
    """This will split the original prompt into the question and
    the information section.

    Args:
        fnames (Set[str]): The files we want to split.
        config (GenerationConfig): Our config object

    Returns:
        tuple(str, str): The question and the information section.
    """
    split_path = PATH_TO_MANIFESTS.joinpath(config.split_file)
    with open(split_path) as f:
        re_str = f.read().splitlines()

    re_str = '|'.join(re_str)
    regex = re.compile(re_str)

    prompts, remainders = [], []

    for fname in fnames:
        with open(fname) as f:
            prompt = f.read().splitlines()

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

        prompts.append(prompt[:prompt_idx])
        remainders.append(prompt[prompt_idx:])
    
    return prompts, remainders

def generate_few_shot_prompts(
    prompt_type: str,
    cfg: GenerationConfig,
    probs: Set[str]) -> str:
    """Generating the examples that will be passed to the model before the new summary.

    Args:
        prompt_type (str): The determined type of the problem.
        cfg (GenerationConfig): The configuration for this generation.
        probs (Set[str]): The human problems to choose from.

    Returns:
        str: The formatted few shot examples for this generation.
    """
    # TODO: Implement the problem types and group similar
    # types of problems together
    category_path = PATH_TO_MANIFESTS.joinpath(cfg.category_file)
    with open(category_path) as f:
        prompt_cfg = yaml.safe_load(f)
    
    # probs = list(probs)
    # If it's a general problem choose any examples
    # if prompt_type == 'general':
        # example_prompts = random.sample(probs, cfg.num_few_shot)
# 
    # logger.debug(f'Using {example_prompts} for few shotting')
# 
    # orig_fnames = list(map(lambda x: f'{x}/question.txt', example_prompts))
    # orig_prompts, _ = split_prompts(orig_fnames, cfg)
# 
    # sum_fnames = list(map(lambda x: f'{x}/{cfg.summary_types[0]}.txt', example_prompts))
    # sum_prompts, _ = split_prompts(sum_fnames, cfg)

    # Here we are forcing the user of picking specific few shot probs
    example_prompts = random.sample(probs, cfg.num_few_shot)
    logger.debug(f'Using {example_prompts} for few shotting')

    sum_prompts, _ = split_prompts(example_prompts, cfg)

    def get_question(x):
        x = x.replace('summary', 'question')
        return x.replace('expert', 'question')

    orig_fnames = list(map(get_question, example_prompts))
    orig_prompts, _ = split_prompts(orig_fnames, cfg)

    output = [
        cfg.prompt_prefix+orig+'\n'+cfg.completion_prefix+summary 
        for orig, summary in zip(orig_prompts, sum_prompts)
    ]
    
    for text, num in zip(output, example_prompts):
        if not check_ascii(text):
            logger.warning(f'Problem {num} was not ascii.')

    output_str = cfg.few_shot_suffix.join(output)
    return output_str

def generate_prompts(
    prompts: List[str],
    prompt_types: List[str],
    human_probs: Set[str],
    cfg: GenerationConfig) -> List[str]:
    output_prompts = []

    with open('/media/HD/Documents/Prompt-Summarization/data/experiments/good-few-shot.csv') as f:
        new_few_shot_probs = f.read().splitlines()

    add_data_dir = lambda x: os.path.join(PATH_TO_DATA, x)
    new_few_shot_probs = list(map(add_data_dir, new_few_shot_probs))

    for prompt, ptype in zip(prompts, prompt_types):
        few_shot_str = generate_few_shot_prompts(
            ptype,
            cfg,
            new_few_shot_probs
            # human_probs
        )
        prompt_str = cfg.header + "\n" + few_shot_str
        prompt_str += f"{cfg.few_shot_suffix}{cfg.prompt_prefix}{prompt}\n{cfg.completion_prefix}"
        prompt_str = remove_starting_and_ending_whitespace(prompt_str)
        prompt_str = ensure_ascii(prompt_str)

        output_prompts.append(prompt_str)
    
    return output_prompts

def remove_starting_and_ending_whitespace(prompt: str) -> str:
    """Remove ending whitespace from string.

    Args:
        prompt (str): prompt to remove from

    Returns:
        str: The resulting string
    """
    s = prompt.rstrip()
    return s.lstrip()

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

def convert_to_apps_format(prompts: Set[str]) -> Set[str]:
    output = set()
    for prompt in prompts:
        new_prompt = prompt.replace('data/human_generated', 'APPS')
        output.add(new_prompt + '/question.txt')
    
    return output

def validate_prompts(cfg: GenerationConfig) -> Tuple[Set[str], int]:
    """Read the specified prompts and determine how many more we need to choose.

    Args:
        cfg (GenerationConfig): The configuration object.

    Returns:
        tuple[set[str], int]: The set of paths to the problems we want to generate for,
        and the number of remaining prompts we have to choose.
    """
    prompts = {}
    num_prompts = cfg.num_prompts
    
    manifest_path = PATH_TO_MANIFESTS.joinpath(cfg.prompt_manifest)
    if manifest_path.is_file():
        # Read the lines from the prompt file
        with open(manifest_path) as f:
            prompts = f.read().splitlines()

    add_data_dir = lambda x: os.path.join(PATH_TO_DATA, x)

    prompts = set(map(add_data_dir, prompts))
    remaining_prompts = num_prompts - len(prompts)

    # We provide every example to use
    if num_prompts == -1 or remaining_prompts == 0:
        logger.info(f'Only using prompts specified in {manifest_path}')
        return prompts, 0

    # We provided too many examples
    if remaining_prompts < 0:
        logger.critical((
            f'You provided {len(prompts)} prompts in the promptFile. ',
            f'But only specified {cfg.num_prompts} in your config file. ',
            'Only selecting the number specified.'
        ))
        sys.exit(1)

    return prompts, remaining_prompts

def select_code_prompts(prompts: Set[str], num_remaining: int, available_prompts: Set[str]) -> set[str]:
    """Select prompts to generate code for.

    Args:
        prompts (set[str]): Prompts already selected.
        num_remaining (int): Number of prompts to select.
        available_prompts (set[str]): Completed problems to choose from.

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

def generate_example_code(prompts: set[str], available_prompts: set[str], cfg: CodexConfig) -> tuple[list[str], list[str]]:
    """Generate the prompt to pass to the API from the prompts selected.

    Args:
        prompts (set[str]): The filenames of the prompts to generate code for.
        available_prompts (set[str]): The prompts available to select for few shot.
        cfg (CodexConfig): The configuration object.

    Returns:
        tuple[list[str], list[str]]: The list of string prompts to be passed to the model.
        The list of prompts used to generate the strings.
    """
    code_prompts = []
    prompt_paths = []
    for prompt in prompts:
        logger.info(f'Generating code for prompt: {prompt}')
        for fname in cfg.summary_types:
            logger.debug(f'Generating for file {fname}')
            prompt_path = Path(prompt, fname+'.txt')

            # Remove current prob from few shot pool
            # TODO: Should we remove from the available prompts if we are using that prompt
            # for another quesiton? Currenty we only remove the current prompt.
            few_shot_list = generate_few_shot(available_prompts - {prompt}, prompt_path, cfg)
            few_shot_str = cfg.few_shot_suffix.join(few_shot_list)

            prompt_text = read_code_files(prompt, prompt_path, cfg, read_solution=False)

            prompt_str = cfg.header + few_shot_str + prompt_text
            prompt_str = remove_starting_and_ending_whitespace(prompt_str)
            code_prompts.append(prompt_str)
            prompt_paths.append(str(prompt_path))

    return code_prompts, prompt_paths

def generate_few_shot(available_prompts: set[str], fname: Path, cfg: CodexConfig) -> list[str]:
    """Generating few shot examples.

    Args:
        available_prompts (set[str]): Set of prompts to choose from.
        fname (Path): The path to the current example we are generating few shot for
        cfg (CodexConfig): The configuration object.

    Returns:
        list[str]: The list of few shot prompts.
    """
    if cfg.num_few_shot == 0:
        return []
    
    available_prompts = list(available_prompts)
    few_shot_examples = random.sample(available_prompts, cfg.num_few_shot)
    
    logger.debug(f'Using {few_shot_examples} for few shot examples.')

    # TODO: Currently we generate few shot examples by reading the summaries.
    # The summary type is defined in the config file. Should we change this
    # to have different few shot examples if we are using the original question?
    examples = [read_code_files(ex, fname, cfg) for ex in few_shot_examples]
    
    return examples

def read_code_files(prompt: str, question_path: Path, cfg: CodexConfig, read_solution: bool=True) -> str:
    """Read the appropriate files from the prompt dir and format into string.

    Args:
        prompt (str): The directory to read from.
        question_path (Path): Path to the file to read
        cfg (CodexConfig): The configuration object.
        read_solution (bool, optional): Whether or not to read solutions.json. Defaults to True.

    Returns:
        str: The str to be passed as input.
    """
    logger.info(f'Generating prompt for file: {question_path}')
    with open(question_path) as f:
        question = f.read()

    code_prefix = get_code_prefix(prompt, cfg.completion_prefix)

    prompt_str  = f'{cfg.prompt_prefix}\n{question}\n{cfg.prompt_suffix}'
    
    if read_solution:
        code_path = Path(prompt, 'solutions.json')
        try:
            codes = json.load(open(code_path))
            min_code_len = 1e6
            # Pick the shortest solution
            for c in codes:
                if len(c) < min_code_len:
                    code = c
            code = format_solution(code)
            prompt_str += f'\n{code}\n'
        except FileNotFoundError:
            logger.error(f'The code solution for prompt {prompt} does not exist. Not including it in few shot examples.')
    else:
        prompt_str += f'\n{code_prefix}'
        
    return prompt_str

def format_solution(code_str: str) -> str:
    """Format the solution to match the format of codex.

    Args:
        code_str (str): The code string to format.

    Returns:
        str: The formatted code string.
    """
    if ('def' in code_str) or code_str.startswith('class'):
        return code_str
    code_arr = code_str.splitlines()
    code = 'def code():\n    ' + '\n    '.join(code_arr)
    return code

def get_code_prefix(prompt: str, default: str) -> str:
    """Return the prefix for code generation.

    Args:
        prompt (str): The problem directory to read from.
        default (str): The default prefix to use if the starter code doesn't exist.

    Returns:
        str: The code prefix used for code generation.
    """
    starter_code = Path(prompt, 'starter_code.py')
    prefix = default
    if starter_code.exists():
        with open(starter_code) as f:
            prefix = f.read().strip()
    else:
        logger.warning(f'The problem {prompt} did not have starter_code.py!')
    return prefix

def log_summary(prompt, extra, output_dir):
    logger.info(f'PROMPT:\n{prompt}')
    logger.info(f'EXTRA:\n{extra}')
    logger.info(f'OUTPUT DIR: {output_dir}')

def log_codes(prompts, output_dirs):
    for p, out in zip(prompts, output_dirs):
        logger.debug(f'Prompt for output {out}')
        logger.debug(f'\n{p}')

@hydra.main(config_path="../configs", config_name="gpt3")
def main(cfg: ExperimentConfig):
    prompts, extras, output_dirs = generate_summary_prompt(cfg.generation_params)
    logger.info('BEGIN TEST')
    for prompt, extra, output_dir in zip(prompts, extras, output_dirs):
        log_summary(prompt, extra, output_dir)
    logger.info('END TEST')

if __name__ == "__main__":
    register_configs()
    main()