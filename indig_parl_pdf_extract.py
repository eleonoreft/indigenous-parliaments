#!/usr/local/bin/python3

import re
import logging

import pandas as pd

from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage
from io import BytesIO

import indig_parl_utils as utils


def pdf_to_text(path):
    """Code source: https://towardsdatascience.com/pdf-preprocessing-with-python-19829752af9f

    Arguments:
        path {[type]} -- [description]

    Returns:
        [type] -- [description]
    """
    manager = PDFResourceManager()
    retstr = BytesIO()
    layout = LAParams(all_texts=True)
    device = TextConverter(manager, retstr, laparams=layout)
    filepath = open(path, 'rb')
    interpreter = PDFPageInterpreter(manager, device)
    for page in PDFPage.get_pages(filepath, check_extractable=True):
        interpreter.process_page(page)
    text = retstr.getvalue()
    filepath.close()
    device.close()
    retstr.close()
    return text


def prepare_raw_text(text, store_path=''):
    re_pg_header = r'\s[A-Z][a-z]+,{0,1}\s[A-Z][a-z]+\s\d{1,2},\s[1,2][0,9]\d{2}\s+Nunavut Hansard'
    re_pg_footer = r'\n(?:Page){0,1}\s+(?:\d{2,4})\s+\n'

    cleaned_text = re.sub(re_pg_header, ' ', text)
    cleaned_text = re.sub(re_pg_footer, '\n', cleaned_text)
    if store_path:
        utils.send_text_to_file(store_path, cleaned_text)
    cleaned_text = cleaned_text.replace('\n', ' ')

    return cleaned_text


def get_pattern_text(pattern, search_text):
    pat_complied = re.compile(pattern)
    pat_match = pat_complied.search(search_text)
    if pat_match:
        return pat_match.group(1)
    return None


def get_oral_q_df(text, d_str, tmp_dir='tmp/'):
    oral_q_sec = r'Item 6: Oral Questions\s+(.*?)(?:\s+Item \d{1,2}:)'
    q_titles = r'\s*(Question\s+\d{1,3}\s*\S\s\d\(\d\)):'
    section_title = r'Item \d{1,2}:'
    speaker_headers = r'\s*((?:M[r|s]s{0,1}\.{0,1}|Hon\.{0,1}|Honourable|Speaker)(?:\s+(?:O\S){0,1}[A-Z]\w+?\.{0,1}){0,2})\s*(?:\(\w+\)){0,1}:'

    oral_questions = get_pattern_text(oral_q_sec, text)
    if oral_questions:
        df_list = []
        title = 'Item 6: Oral Questions'
        question_list = re.split(q_titles, text)
        for idx in range(len(question_list)):
            if title in question_list[idx]:
                logging.debug('Title in idx: %s' % idx)
                # print(idx, 'entry:', question_list[idx])
                if idx > 0:
                    logging.debug('Previous entry: %s' % question_list[idx-1])
                if idx < len(question_list)-1:
                    logging.debug('Next entry: %s' % question_list[idx+1])
                if idx == 0:
                    question_list = question_list[1:]
                else:
                    question_list = question_list[idx-1:]
                    question_list[1] = question_list[idx].replace(title, '')
                break
        last_item = question_list[len(question_list)-1]
        split_l_item = re.split(section_title, last_item)
        question_list[len(question_list)-1] = split_l_item[0]
        utils.send_text_to_file(tmp_dir+d_str + 'pre_q_split_raw.txt',
                                question_list, data_type='list')
        for idx in range(len(question_list)):
            if not 'Question' == question_list[idx][:8]:
                speaker_pattern = re.compile(speaker_headers)
                speaker_match = speaker_pattern.search(question_list[idx])
                if speaker_match:
                    (start, _) = speaker_match.span()
                    q_tail = question_list[idx][:start]
                    # print('Question tail:', q_tail)
                    dialog = question_list[idx][start:]
                    # print('Old question:', question_list[idx-1])
                    question_list[idx-1] += ': ' + q_tail
                    # print('New question:', question_list[idx-1])
                    question_list[idx] = dialog
        utils.send_text_to_file(tmp_dir+d_str +'q_split_raw.txt',
                                question_list, data_type='list')
        even_q_list = question_list[1::2]
        odd_q_list = question_list[::2]
        q_dict = dict(zip(odd_q_list, even_q_list))
        logging.debug('split oral questions by question')
        for q in q_dict.keys():
            diag = q_dict[q]
            diag_list = re.split(speaker_headers, diag)
            if diag_list[0] == '':
                diag_list.pop(0)
            even_diag_list = diag_list[1::2]
            odd_diag_list = diag_list[::2]
            diag_tup_list = list(zip(odd_diag_list, even_diag_list))
            q_col_list = [q] * len(diag_tup_list)
            combined = list(
                zip(q_col_list, odd_diag_list, even_diag_list))
            partial_df = pd.DataFrame(
                combined, columns=['question', 'speaker', 'speech'])
            df_list.append(partial_df)
        logging.debug('split question dialogs and dialog splits')
        return pd.concat(df_list)
    else:
        print('Error processing PDF Oral Questions section.')
        logging.debug('Error processing PDF Oral Questions section.')
        return pd.DataFrame(columns=['question', 'speaker', 'speech'])


def process_pdf(pdf_loc, date_str, coding='utf-8', tmp_dir='tmp/'):
    try:
        raw_text = pdf_to_text(pdf_loc)
        raw_text = raw_text.decode(encoding=coding)
        # send_text_to_file('Nunavut/clean_csvs/'+date_str +
        #                   '-raw_text.txt', raw_text)
        # print('raw text sent')
        store_to = tmp_dir + date_str + 'rem_hd_ft_raw_text.txt'
        rm_hd_nl_text = prepare_raw_text(raw_text, store_path=store_to)
        # send_text_to_file('Nunavut/clean_csvs/'+date_str +
        #                   'rem_nl_raw_text.txt', rm_hd_nl_text)
        # print('Raw text no newlines sent')
        if rm_hd_nl_text.find("Item 6: Oral Questions") > -1:
            utils.send_text_to_file(tmp_dir+date_str+'-raw_text.txt', raw_text)
            logging.debug('Raw pdf text sent %s' % date_str)
            utils.send_text_to_file(tmp_dir+date_str+'rem_nl_raw_text.txt',
                                    rm_hd_nl_text)
            logging.debug('Raw text no newlines sent %s' % date_str)
            return get_oral_q_df(rm_hd_nl_text, date_str)
        else:
            print('Oral Questions section not present in PDF %s.' % pdf_loc)
            return pd.DataFrame(columns=['question', 'speaker', 'speech'])
    except Exception as e:
        print('ERROR: Error reading/accessing pdf document for %s. [%s].' %
              (date_str, pdf_loc))
        logging.debug('ERROR: Error accessing pdf document for %s. [%s].' %
                      (date_str, pdf_loc))
        logging.debug(e)
        return pd.DataFrame(columns=['question', 'speaker', 'speech'])
