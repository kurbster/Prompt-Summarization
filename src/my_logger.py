#!/usr/bin/env python3
import os
import yaml
import logging.config

from datetime import datetime

def setup():
    if not os.path.exists('logs'):
        os.mkdir('logs')
    
    config_file = 'logging.yaml'
    cwd = os.path.split(os.getcwd())[1]
    if cwd == 'gpt':
        config_file = '../logging.yaml'

    with open(config_file) as f:
        cfg = yaml.safe_load(f)

    str_time = datetime.now().strftime('%m-%d-%Y_%H:%M:%S')
    fname = f'logs/{str_time}.log'
    test_fname = f'logs/test-{str_time}.log'

    cfg['handlers']['file']['filename'] = fname
    cfg['handlers']['testFile']['filename'] = test_fname
    logging.config.dictConfig(cfg)

setup()
