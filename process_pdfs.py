#!/usr/local/bin/python3

import re

import indig_parl_utils as utils
from indig_parl_re import text_split

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
    # Drop the first element
    quest_dialog_list = text_split(oral_q_section, question_head_ptrn)[1:]

    utils.send_text_to_file('NWT/tmp/'+str_date+'raw_oral_questions_list.txt',
                            quest_dialog_list, data_type='list')
    # repair titles
    new_list = []
    # repair speakers titles
    counter = 0
    for idx in range(len(quest_dialog_list)):
        if counter < 4:
            counter += 1
        else:
            counter = 1
        if counter % 3 == 0:
            new_list.append(
                quest_dialog_list[idx-2] + quest_dialog_list[idx-1])
            new_list.append(quest_dialog_list[idx] + quest_dialog_list[idx+1])

    quest_dialog_list = new_list
    utils.send_text_to_file('NWT/tmp/'+str_date+'fixed_oral_questions_list.txt',
                            quest_dialog_list, data_type='list')

    speakers_table = []
    for item in quest_dialog_list:
        if item[:8] == 'Question':
            loc1 = item
        else:
            speech_lst = text_split(item, speaker_ptrn)
            loc2 = ''
            loc3 = ''
            for speech in speech_lst:
                if speech.split(' ')[0] in SPEAKER_TITLES:
                    loc2 = speech
                else:
                    loc3 = speech
                    speakers_table.append((loc1, loc2, loc3))

    utils.csv_from_list(csv_name, speakers_table,
                        header_row=['Question', 'Speaker', 'Speech'])
    pdfs_logger.debug('Created CSV file: %s' % csv_name)
