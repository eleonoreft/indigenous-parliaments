#!/usr/local/bin/python3

import re

import indig_parl_utils as utils
from indig_parl_re import get_pattern_match, text_rem_patterns, text_split

from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage
from io import BytesIO

from indig_parl_logger import get_logger


SPEAKER_TITLES = ['MR.', 'MS.', 'MRS.', 'HON.', 'HONOURABLE']

pdfs_logger = get_logger("Process_PDF_Handards",
                         a_log_file='NWT/logs/proc_pdfs_hansards_debug.log')


def pdf_to_text(path):
    """Code source: https://towardsdatascience.com/pdf-preprocessing-with-python-19829752af9f
    """
    manager = PDFResourceManager()
    retstr = BytesIO()
    layout = LAParams(all_texts=True)
    device = TextConverter(manager, retstr, laparams=layout)
    with open(path, 'rb') as f_in:
        interpreter = PDFPageInterpreter(manager, device)
        for page in PDFPage.get_pages(f_in, check_extractable=True):
            interpreter.process_page(page)
    raw_text = retstr.getvalue()
    device.close()
    retstr.close()
    raw_text = raw_text.decode(encoding='utf-8')
    return raw_text


def process_pdf_oral_q(oral_q_section, question_head_ptrn, speaker_ptrn,
                       csv_name, str_date):


    title_pttrn_1 = '\w+\s\d\d{0,1}\,{1}\s\d{4}   HANSARD   \d{2,4}'
    title_pttrn_2 = '\d{2,4}   HANSARD   \w+\s\d\d{0,1}\,{1}\s\d{4}'
    ques_title_pttrn = '^(?:  (.*?)  )'

    rem_titles = text_rem_patterns(oral_q_section, rem_patterns=[title_pttrn_1, title_pttrn_2], replace_with='')

    # Drop the first element
    quest_dialog_list = text_split(rem_titles, question_head_ptrn)
    utils.send_text_to_file('Yukon/tmp/'+str_date+'[3]-raw_oral_questions_list.txt',
                            quest_dialog_list, data_type='list')
    
    speakers_table = []

    for num in range(1, len(quest_dialog_list)):
        title = get_pattern_match(quest_dialog_list[num], ques_title_pttrn)
        title = title.group(1)
        title_list = text_split(quest_dialog_list[num], ques_title_pttrn)
        dialog = title_list[2]
        dialog_list = text_split(dialog, speaker_ptrn)
        tracker = 1
        for idx in range(1, len(dialog_list)):
            '''Strating from storage location 1, record only the first (member name) and third items (member dialogue) every three items'''
            if tracker == 1:
                member = dialog_list[idx].strip()[:-1]
                tracker += 1
            elif tracker == 2:
                tracker += 1
            elif tracker == 3:
                member_diag = dialog_list[idx].strip()[:-1]
                speakers_table.append([title, member, member_diag])
                tracker = 1


    utils.csv_from_list(csv_name, speakers_table,
                        header_row=['Question', 'Speaker', 'Speech'])
    pdfs_logger.debug('Created CSV file: %s' % csv_name)
