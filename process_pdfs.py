#!/usr/local/bin/python3

import re

import indig_parl_utils as utils

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


def text_rem_patterns(text, rem_patterns=[]):
    if rem_patterns:
        for pattern in rem_patterns:
            text = re.sub(pattern, ' ', text)
            pdfs_logger.debug('Removed %s' % pattern)
    return text


def text_find_pattern(text, pattern):
    match = re.compile(pattern).search(text)
    if match:
        pdfs_logger.debug('%s match found' % pattern)
        return True
    pdfs_logger.debug('%s match NOT found' % pattern)
    return False


def text_extract_pattern(text, pattern):
    return re.compile(pattern).search(text)


def text_split(text, pattern, mx_split=0):
    # Drop the first element in the list
    return re.split(pattern, text, maxsplit=mx_split)[1:]


def process_pdf_oral_q(oral_q_section, question_head_ptrn, speaker_ptrn,
                       csv_name, str_date):
    quest_dialog_list = text_split(oral_q_section, question_head_ptrn)
    utils.send_text_to_file('NWT/tmp/'+str_date+'raw_oral_questions_list.txt',
                            quest_dialog_list, data_type='list')
    # repair titles
    new_list = []
    add_to = ''
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

    # for item in quest_dialog_list:
    #     if item in SPEAKER_TITLES:
    #         add_to = item
    #     else:
    #         if add_to:
    #             new_list.append(add_to + item)
    #             add_to = ''
    #         else:
    #             new_list.append(item)
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


# if __name__ == '__main__':
#     oral_ques_pattern = r'(Question\s+\d{1,3}.*?:.*?)\s*(M[R|S]S{0,1}\.|HON\.|HONOURABLE)'
#     speaker_pattern = r'((?:M[R|S]S{0,1}\.|HON\.|HONOURABLE).*?):'

#     with open('NWT/oral_ques_sec_01.txt', 'r') as f:
#         str1 = f.read()

#     lst = text_split(str1, oral_ques_pattern)
#     print('List length:', len(lst))
#     print(lst[0])
#     print(lst[1])
#     print(lst[2])
#     print(lst[3])
#     new_list = []
#     add_to = ''
#     for item in lst:
#         if item in TITLES:
#             add_to = item
#         else:
#             if add_to:
#                 new_list.append(add_to + item)
#                 add_to = ''
#             else:
#                 new_list.append(item)
#     print('New list:', len(new_list))
#     speakers_table = []
#     for item in new_list:
#         if item[:8] == 'Question':
#             loc1 = item
#         else:
#             speech_lst = text_split(item, speaker_pattern)
#             loc2 = ''
#             loc3 = ''
#             for speech in speech_lst:
#                 if speech.split(' ')[0] in TITLES:
#                     loc2 = speech
#                 else:
#                     loc3 = speech
#                     speakers_table.append((loc1, loc2, loc3))

#     for row in speakers_table:
#         print(row[1])

    # print(new_list[0])
    # print(new_list[1])
    # print(new_list[2])
    # print(new_list[3])
    # new_list_odd = new_list[::2]
    # new_list_even = new_list[1::2]
    # print('Length odd:', len(new_list_odd))
    # print('Length even:', len(new_list_even))
