#!/usr/local/bin/python3

"""Convert MHT file (Archive HTML) into HTML files
"""

# import requests
import re
import os
import base64

from indig_parl_logger import get_logger
from indig_parl_re import text_split, get_pattern_match, text_rem_patterns

logger_mht = get_logger("Process_MHT", a_log_file='logs/process_mht_debug.log')


def mht_check(text):
    check_str = 'Content-Type: multipart/related'
    if check_str.lower() in text.lower():
        logger_mht.debug('MHT file contains "%s", hence valid.' % check_str)
        return True
    else:
        logger_mht.debug('MHT file contains "%s", hence INVALID.' % check_str)
        return False


def get_boundary(text):
    re_boundary = r'boundary=\"(.*)\"'
    found = re.compile(re_boundary).search(text)
    if found:
        boundry_text = found.group(1)
        logger_mht.debug('Boundry text found: %s' % '--'+boundry_text)
        return '--'+boundry_text
    else:
        logger_mht.debug('No Boundry text found')
        return ''


def extract_files(mht_loc, sub_dir=''):
    patt_loc = r'Content-Location:\s*(.*)\s*\n'
    patt_contnet_type = r'Content-Type:\s*(.*)\s*\n'
    patt_encode = r'Content-Transfer-Encoding:\s*(.*)\s*\n'
    pat_rem = r'=\n'
    with open(mht_loc, 'r') as mht:
        mht_text = mht.read()
        mht_file = mht_check(mht_text)
        boundry_text = get_boundary(mht_text)
        print(">>", boundry_text)
        if mht_file and boundry_text:
            # Drop first and last elements
            files = text_split(mht_text, boundry_text)[1:-1]
            logger_mht.debug('MHT file contains %s files.' % len(files))
            main_dir = '/'.join(mht_loc.split('/')[:-1])
            for idx in range(len(files)):
                file_content = files[idx]
                loc_find = get_pattern_match(file_content, patt_loc)
                encode_find = get_pattern_match(file_content, patt_encode)
                if loc_find and encode_find:
                    file_content = text_rem_patterns(
                        file_content, [pat_rem, patt_contnet_type, patt_loc, patt_encode], '')
                    file_name = loc_find.group(1).split('/')[-1:][0]
                    if idx == 0:
                        main_dir += '/'+file_name.split('.')[0]
                        if not sub_dir:
                            sub_dir = file_name.split('.')[0] + '_files'
                        if not os.path.exists(main_dir):
                            os.mkdir(main_dir)
                        if not os.path.exists(main_dir+'/'+sub_dir):
                            os.mkdir(main_dir+'/'+sub_dir)
                        outfile_path = main_dir+'/'+file_name
                        main_html = outfile_path
                    else:
                        outfile_path = main_dir+'/'+sub_dir+'/'+file_name
                    if 'base64' in encode_find.group(1):
                        # file_content = base64.b64decode(file_content)
                        with open(outfile_path, "wb") as out_f:
                            out_f.write(file_content.encode('utf-8'))
                            logger_mht.debug('Created %s file', outfile_path)
                    else:
                        with open(outfile_path, "w") as out_f:
                            out_f.write(file_content)
                            logger_mht.debug('Created %s file', outfile_path)
                else:
                    logger_mht.debug('Error processing section in file %s.' %
                                     mht_loc)
            return main_html
        else:
            logger_mht.debug(
                'File "%s" isn\'t a valid MHT file. Missing boundary text or \
                    content type header.' % mht_loc)
            print('File "%s" isn\'t a valid MHT file.' % mht_loc)
            return ''


if __name__ == "__main__":
    file_loc = 'Yukon/mhts/[date_short]3-34-037_1.mht'
    outcome = extract_files(file_loc)
    if outcome:
        print('Processing successful')
    else:
        print('Processing failed')
