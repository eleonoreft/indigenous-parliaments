#!/usr/local/bin/python3

"""Adapted form https://www.toptal.com/python/in-depth-python-logging

Returns:
    [type] -- [description]
"""

import logging
import sys
from logging.handlers import RotatingFileHandler


FORMATTER = logging.Formatter(
    "%(asctime)s — %(name)s — %(levelname)s — %(message)s")
LOG_FILE = "default.log"


def get_console_handler(a_formatter=FORMATTER):
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(a_formatter)
    return console_handler


def get_file_handler(a_log_file=LOG_FILE, a_formatter=FORMATTER):
    file_handler = RotatingFileHandler(
        a_log_file, maxBytes=5120000, backupCount=10)
    file_handler.setFormatter(a_formatter)
    return file_handler


def get_logger(logger_name, a_log_file=LOG_FILE, a_formatter=FORMATTER):
    logger = logging.getLogger(logger_name)
    # better to have too much log than not enough
    logger.setLevel(logging.DEBUG)
    logger.addHandler(get_console_handler(a_formatter=a_formatter))
    logger.addHandler(get_file_handler(
        a_log_file=a_log_file, a_formatter=a_formatter))
    # with this pattern, it's rarely necessary to propagate the error up to parent
    logger.propagate = False
    return logger
