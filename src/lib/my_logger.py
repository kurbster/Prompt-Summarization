#!/usr/bin/env python3
import yaml
import logging.config

from datetime import datetime
from pathlib import Path

def setup():
    rel_path_to_src = '../..'
    log_dir = Path(__file__, rel_path_to_src, 'logs').resolve()

    if not log_dir.exists():
        log_dir.mkdir()

    cfg_file = Path(__file__, rel_path_to_src, 'configs/logging.yaml').resolve()

    with open(cfg_file) as f:
        cfg = yaml.safe_load(f)

    str_time = datetime.now().strftime('%m-%d-%Y_%H:%M:%S')
    fname = Path(log_dir, f'{str_time}.log')
    test_fname = Path(log_dir, f'test-{str_time}.log')

    cfg['handlers']['file']['filename'] = fname
    #cfg['handlers']['testFile']['filename'] = str(test_fname)
    logging.config.dictConfig(cfg)

setup()
