#!/usr/bin/local/python3

"""Common Regular Expression functions called by other Indigenous Parliament
modules
"""

import re

from indig_parl_logger import get_logger

re_logger = get_logger("Process_PDF_Handards",
                       a_log_file='NWT/logs/proc_pdfs_hansards_debug.log')


def text_find_pattern(text, pattern):
    match = re.compile(pattern).search(text)
    if match:
        re_logger.debug('%s match found' % pattern)
        return True
    re_logger.debug('%s match NOT found' % pattern)
    return False


def text_extract_pattern(text, pattern):
    return re.compile(pattern).search(text)


def get_pattern_match(text, pattern):
    return re.compile(pattern).search(text)


def text_split(text, pattern, mx_split=0):
    return re.split(pattern, text, maxsplit=mx_split)


def text_rem_patterns(text, rem_patterns=[], replace_with=' '):
    if rem_patterns:
        for pattern in rem_patterns:
            text = re.sub(pattern, replace_with, text)
            re_logger.debug('Removed %s' % pattern)
    return text
