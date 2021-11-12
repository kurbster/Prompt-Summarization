#!/usr/bin/env python3
import os
import yaml
import logging.config

from datetime import datetime

def setup():
    config_file = 'logging.yaml'
    cwd = os.path.split(os.getcwd())[1]
    if cwd == 'gpt':
        config_file = '../logging.yaml'

    with open(config_file) as f:
        cfg = yaml.safe_load(f)

    fname = 'logs/' + datetime.now().strftime('%m-%d-%Y_%H:%M:%S') + '.log'
    cfg['handlers']['file']['filename'] = fname
    logging.config.dictConfig(cfg)

setup()
