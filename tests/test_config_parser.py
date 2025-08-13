# tests/test_config_parser.py
"""
Simple smoke tests - run with pytest
"""
import os
from modules import config_parser

def test_parse_sample():
    # ensure function returns dict even if no configs
    res = config_parser.parse_all_configs("./configs")
    assert isinstance(res, dict)
