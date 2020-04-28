#!/usr/local/bin/python3

import pdftotext
from pdfrw import PdfReader

import re
import pandas as pd
import requests
import csv

from nunavut_hansards import csv_2_date_path_dict

from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage
from io import BytesIO


def get_pdfs_list(source_file):
    location_dict = {}
    lines = 0
    with open(source_file, newline='') as csv_f:
        if lines == 0:
            lines += 1
        else:
            csv_reader = csv.reader(csv_f, delimiter=',', quotechar='"')
            for row in csv_reader:
                location_dict[row[1]] = row[2]

    return location_dict


def get_pdf(url, dte_str):
    r = requests.get(url)
    file_loc = "Nunavut/pdfs/" + dte_str + ".pdf"
    with open(file_loc, 'wb') as f:
        f.write(r.content)
    return file_loc


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


def send_text_to_file(file_path, data, header='', data_type='text'):
    with open(file_path, 'w') as f:
        if header:
            f.write(header.title() + '\n\n')
        if data_type == 'list':
            for line in data:
                f.write(line + '\n')
        elif data_type == 'dict':
            for item in data.keys():
                f.write(item + ': ' + data[item] + '\n')
        elif data_type == 'tup_list':
            for (a, b) in data:
                f.write(a+' - '+b+'\n')
        else:
            f.write(data)


def get_pattern_text(pattern, search_text):
    pat_complied = re.compile(pattern)
    pat_match = pat_complied.search(search_text)
    if pat_match:
        return pat_match.group(1)
    return None


def prepare_raw_text(text, store_path=''):
    # re_pg_header = r'\s[A-Z][a-z]+,\s[A-Z][a-z]+\s\d{1,2},\s[1,2][0,9]\d{2}\s+Nunavut Hansard'
    re_pg_header = r'\s[A-Z][a-z]+,{0,1}\s[A-Z][a-z]+\s\d{1,2},\s[1,2][0,9]\d{2}\s+Nunavut Hansard'
    # re_pg_footer = r'\n\s+\s\d{2,4}\s+\n'
    # re_pg_footer = r'\nPage{0,1}\s+(?:\d{2,4})\s+\n'
    re_pg_footer = r'\n(?:Page){0,1}\s+(?:\d{2,4})\s+\n'

    cleaned_text = re.sub(re_pg_header, ' ', text)
    cleaned_text = re.sub(re_pg_footer, '\n', cleaned_text)
    if store_path:
        send_text_to_file(store_path, cleaned_text)
    # 3. Remove newlines characters from text
    cleaned_text = cleaned_text.replace('\n', ' ')

    return cleaned_text


def get_oral_q_df(text, d_str):
    oral_q_sec = r'Item 6: Oral Questions\s+(.*?)(?:\s+Item \d{1,2}:)'
    # q_titles = r'(\s*Question \d{1,3}\s.+?:.*?)(?:Mr\.|Ms\.|Hon\.|Honourable)'
    # q_titles = r'(\s*Question \d{1,3}\s.+?:.*?\(.+?\))'
    # q_titles = r'(\s*Question \d{1,3}\s.+?:.*?(?:\(.+?\)){0,1}\s\s+)'
    # q_titles = r'(\s*Question \d{1,3}\s.+?:(?:\s+\w+)+\s+(?:\(\w+\)){0,1})'
    # q_titles = r'(\s*Question \d{1,3}\s.+?:(?:\s+\w+\S{0,1}\w)+\s+(?:\(\w+,{0,1}\s*\w{0,1}\)){0,1})'
    # q_titles = r'\s*(Question\s+\d{0,3}\s\S\s\d\(\d\):\s(?:\w+(?:\S)*\s+)+(?:\(\w+(?:(?:\S)*\s\w+){0,1}){0,1}\))'
    # q_titles = r'\s*(Question\s+\d{1,3}\s\S\s\d\(\d\):\s*(?:\s\w*(?:\S\s){0,1})+(?:\s*\S\w+\S)*?(?:\s*\(\w*(?:, \w){0,1}\)))'
    # q_titles = r'\s*(Question\s+\d{1,3}\s\S\s\d\(\d\):\s*(?:\s\w*(?:\S\s){0,1})+(?:\s*\S\w+\S)*?(?:\s*\(\w*(?:, \w){0,1}\))*)'
    q_titles = r'\s*(Question\s+\d{1,3}\s*\S\s\d\(\d\):(?:\s*\S*)\s*(?:\s\w*(?:\S\s){0,1})+(?:\s*\S\w+\S)*?(?:\s*\(\w*(?:, \w){0,1}\))*)'
    # speaker_headers = r'((?:Honorable|Hon\.|Mr\.|M[r]{0,1}s\.){0,1}\s*(?:[A-Z]\w+){0,1}\s*[A-Z]\w+:)'
    # speaker_headers = r'(\s*(?:M[r|s]s{0,1}\.|Hon\.|Honourable){0,1}(?:\s+[A-Z]\w+?){1,2}\s*(?:\(\w+\)){0,1}:)'
    # speaker_headers = r'(\s+(?:M[r|s]s{0,1}\.|Hon\.|Honourable|Speaker)(?:\s+[A-Z]\w+?){0,2}\s*(?:\(\w+\))?:)'
    speaker_headers = r'\s*((?:M[r|s]s{0,1}\.|Hon\.|Honourable|Speaker)(?:\s+[A-Z]\w+?){0,2})\s*(?:\(\w+\))?:'

    oral_questions = get_pattern_text(oral_q_sec, text)
    if oral_questions:
        df_list = []
        send_text_to_file('Nunavut/clean_csvs/'+d_str +
                          'oral_q_raw.txt', oral_questions)
        print('oral questions found')
        q_list = re.split(q_titles, oral_questions)
        if q_list[0] == '':
            q_list.pop(0)
        q_list = [q.strip() for q in q_list]
        # For every item in question list,
        #   check if the item is a question,
        #       if the item is a question, check id thier is a name at the end,
        #           if there is a name, remove it and add it to the start of the next item in the list (dialog)
        for idx in range(len(q_list)):
            if 'Question' == q_list[idx][:8]:
                speaker_pattern = re.compile(speaker_headers)
                speaker_match = speaker_pattern.search(q_list[idx])
                if speaker_match:
                    (start, _) = speaker_match.span()
                    print('Question with speaker:', q_list[idx])
                    speaker_portion = q_list[idx][start:]
                    print('Speaker portion:', speaker_portion)
                    q_list[idx] = q_list[idx][:start]
                    print('New question:', q_list[idx])
                    print('Next list item', q_list[idx+1])
                    q_list[idx+1] = speaker_portion + q_list[idx+1]
                    print('Next list item updated:', q_list[idx+1])

        send_text_to_file('Nunavut/clean_csvs/'+d_str +
                          'q_split_raw.txt', q_list, data_type='list')
        even_q_list = q_list[1::2]
        odd_q_list = q_list[::2]
        q_dict = dict(zip(odd_q_list, even_q_list))
        print('split oral questions by question')
        for q in q_dict.keys():
            diag = q_dict[q]
            diag_list = re.split(speaker_headers, diag)
            if diag_list[0] == '':
                diag_list.pop(0)
            # send_text_to_file('Nunavut/clean_csvs/'+date_str+q[:13]+'.txt',
            #                   diag_list, header=q, data_type='list')
            even_diag_list = diag_list[1::2]
            odd_diag_list = diag_list[::2]
            # print('len evens:', len(even_diag_list))
            # for a in even_diag_list:
            #     print(a)
            # print('len odds:', len(odd_diag_list))
            # for a in odd_diag_list:
            #     print(a)
            diag_tup_list = list(zip(odd_diag_list, even_diag_list))
            # print('tuple list length:', len(diag_tup_list))
            # file_loc = 'Nunavut/clean_csvs/'+d_str
            # file_loc += 'q_dialog_split_'+q[:13]+'_raw.txt'
            # send_text_to_file(file_loc, diag_tup_list,
            #                   data_type='tup_list')
            q_col_list = [q] * len(diag_tup_list)
            combined = list(
                zip(q_col_list, odd_diag_list, even_diag_list))
            partial_df = pd.DataFrame(
                combined, columns=['question', 'speaker', 'speech'])
            df_list.append(partial_df)
        print('split question dialogs and dialog splits')
        return pd.concat(df_list)
    else:
        print('Error processing Oral Questions section.')
        return pd.DataFrame(columns=['question', 'speaker', 'speech'])


def process_pdf(pdf_loc, date_str, coding='utf-8'):

    try:
        # 1. Read PDF as text, convert to UTF-8
        raw_text = pdf_to_text(pdf_loc)
        raw_text = raw_text.decode(encoding=coding)
        # send_text_to_file('Nunavut/clean_csvs/'+date_str +
        #                   '-raw_text.txt', raw_text)
        # print('raw text sent')
        # 2. Remove header and footer strings from text
        store_to = 'Nunavut/clean_csvs/'+date_str + 'rem_hd_ft_raw_text.txt'
        rm_hd_nl_text = prepare_raw_text(raw_text, store_path=store_to)
        # send_text_to_file('Nunavut/clean_csvs/'+date_str +
        #                   'rem_nl_raw_text.txt', rm_hd_nl_text)
        # print('Raw text no newlines sent')
        # 5. Check if Oral Questions sections are present in the text
        if rm_hd_nl_text.find("Item 6: Oral Questions") > -1:
            send_text_to_file('Nunavut/clean_csvs/'+date_str +
                              '-raw_text.txt', raw_text)
            print('Raw text sent', date_str)
            send_text_to_file('Nunavut/clean_csvs/'+date_str +
                              'rem_nl_raw_text.txt', rm_hd_nl_text)
            print('Raw text no newlines sent', date_str)
            # 4. Get attendance text
            # attendance_txt = get_pattern_text(attend_para, raw_text)
            # if attendance_txt:
            #     send_text_to_file('Nunavut/attendance_text.txt', attendance_txt)
            #     print('attendance text found')
            # else:
            #     print('no attendance text found')
            # 5. TODO: Get speaker names
            # 6. Get Oral Questions section
            return get_oral_q_df(rm_hd_nl_text, date_str)
        else:
            print('Oral Questions section not present in PDF %s.' % pdf_loc)
            return pd.DataFrame(columns=['question', 'speaker', 'speech'])
    except Exception as e:
        print('ERROR: Error reading/accessing pdf document for %s. [%s].' %
              (date_str, pdf_loc))
        print(e)
        return pd.DataFrame(columns=['question', 'speaker', 'speech'])


def old_main():
    re_pg_header = r'\s[A-Z][a-z]+,\s[A-Z][a-z]+\s\d{1,2},\s[1,2][0,9]\d{2}\s+Nunavut Hansard'
    re_pg_footer = r'\n\s+\s\d{2,4}\s+\n'
    attend_para = r'Members Present:(.*)?(?:>>House commenced|Item 1:)'
    oral_q_sec = r'Item 6: Oral Questions\s+(.*?)(?:\s+Item \d{1,2}:)'
    # q_titles = r'(\s*Question \d{1,3}\s.+?:.*?)(?:Mr\.|Ms\.|Hon\.|Honourable)'
    q_titles = r'(\s*Question \d{1,3}\s.+?:.*?\(.+?\))'
    # speaker_headers = r'((?:Honorable|Hon\.|Mr\.|M[r]{0,1}s\.){0,1}\s*(?:[A-Z]\w+){0,1}\s*[A-Z]\w+:)'
    speaker_headers = r'(\s*(?:M[r|s]s{0,1}\.|Hon\.|Honourable){0,1}(?:\s+[A-Z]\w+?){1,2}\s*(?:\(\w+\)){0,1}:)'

    # 1. Read PDF as text, convert to UTF-8
    text = pdf_to_text("Nunavut/pdfs/20111026.pdf")
    text = text.decode('utf-8')

    send_text_to_file('Nunavut/raw_tex.txt', text)
    print('raw text sent')

    # 2. Remove header and footer strings from text
    text = re.sub(re_pg_header, ' ', text)
    text = re.sub(re_pg_footer, '\n', text)
    send_text_to_file('Nunavut/rem_hd_ft_raw_text.txt', text)

    # 3. Remove newlines characters from text
    text = text.replace('\n', ' ')
    send_text_to_file('Nunavut/rem_nl_raw_text.txt', text)
    print(' raw text no newlines sent')

    # 5. Check if Oral Questions sections are present in the text
    if text.find("Item 6: Oral Questions") > -1:
        # # 5.1 Oral text section present
        # # 5.1.1 Check for attendance text
        # attend_pattern = re.compile(attend_para)
        # attend_match = attend_pattern.search(text)
        # if attend_match:
        #     # 5.1.1.1 attendance text present
        #     # TODO: 5.1.1.1.1 Extract speaker names (maybe)
        #     attendance_txt = attend_match.group(1)
        #     send_text_to_file('Nunavut/attendance_text.txt', attendance_txt)
        #     print('attendance text found')
        # else:
        #     # 5.1.1.2 No attendance text present
        #     print('no attendance text found')
        attendance_txt = get_pattern_text(attend_para, text)
        if attendance_txt:
            send_text_to_file('Nunavut/attendance_text.txt', attendance_txt)
            print('attendance text found')
        else:
            print('no attendance text found')

        # 5.1.2 Check for oral questions section
        oral_q_pattern = re.compile(oral_q_sec)
        oral_q_match = oral_q_pattern.search(text)
        if oral_q_match:
            # 5.1.2.1 oral questions found
            # 5.1.2.1.1 Extract oral questions
            oral_questions = oral_q_match.group(1)
            send_text_to_file('Nunavut/oral_questions.txt', oral_questions)
            print('oral questions found')
            # 5.1.2.1.2 Separate into question groups
            q_list = re.split(q_titles, oral_questions)
            if q_list[0] == '':
                q_list.pop(0)
            q_list = [a.strip() for a in q_list]
            send_text_to_file('Nunavut/questions_split.txt',
                              q_list, data_type='list')
            print('split oral questions by question')
            even_q_list = q_list[1::2]
            odd_q_list = q_list[::2]
            q_dict = dict(zip(odd_q_list, even_q_list))
            print('len q_list:', len(q_list))
            print('len q_list odds:', len(odd_q_list))
            print('len q_list evens:', len(even_q_list))
            print('len q_dict:', len(q_dict))
            send_text_to_file('Nunavut/questions_split_2.txt',
                              q_dict, data_type='dict')
            print('split oral questions by question again')
            # 5.1.2.1.3 Separate question groups in dialogs (speaker:speech)
            # 5.1.2.1.4 TODO: send to file
            for q in q_dict.keys():
                diag = q_dict[q]
                diag_list = re.split(speaker_headers, diag)
                if diag_list[0] == '':
                    diag_list.pop(0)
                print('length ('+q[:13]+'):', len(diag_list))
                send_text_to_file('Nunavut/dialog_split_'+q[:13]+'.txt',
                                  diag_list, header=q, data_type='list')
                even_diag_list = diag_list[1::2]
                odd_diag_list = diag_list[::2]
                print('len evens:', len(even_diag_list))
                print('len odds:', len(odd_diag_list))
                diag_tup_list = list(zip(odd_diag_list, even_diag_list))
                print('tuple list length:', len(diag_tup_list))
                send_text_to_file('Nunavut/Q_dialog_split_'+q[:13]+'.txt',
                                  diag_tup_list, data_type='tup_list')
            print('split question dialogs and dialog splits')
        else:
            print('no oral questions found')
    else:
        # 5.2 No oral text section present
        print('oral questions section not present')

    # with open('Nunavut/pdfs/20111026.pdf', 'rb') as f:
    #     pdf1 = pdftotext.PDF(f)

    # print('Page count:', len(pdf1))

    # for count in range(5):
    #     print('PAGE', count, '\n', pdf1[count], '\n\n')

    # # print('ALL TEXT\n', '\n\n'.join(pdf1))

    # pdf2 = PdfReader('Nunavut/pdfs/20111026.pdf')
    # print('Page count:', len(pdf2.pages))

    # for count in range(5):
    #     print('PAGE', count, '\n', pdf2.pages[count], '\n\n')


def main():
    # path_dct = csv_2_date_path_dict('Nunavut/5-Assembly.csv')
    # path_dct = csv_2_date_path_dict('Nunavut/special_file.csv')
    # path_dct = csv_2_date_path_dict('Nunavut/archives.csv')
    # path_dct = csv_2_date_path_dict('Nunavut/archives_4th.csv')
    # path_dct = csv_2_date_path_dict('Nunavut/archives_3rd.csv')
    path_dct = csv_2_date_path_dict('Nunavut/archives_2nd.csv')
    # path_dct = get_pdfs_list('Nunavut/archives_2nd.csv')
    # path_dct = csv_2_date_path_dict('Nunavut/archives_1st.csv')
    for dte in path_dct:
        pdf_name = get_pdf(path_dct[dte], dte)
        hansard_df = process_pdf(pdf_name, dte)
        if not hansard_df.empty:
            hansard_df.to_csv("Nunavut/clean_csvs/"+dte +
                              ".csv", encoding='utf-8-sig')
            print("CSV saved for: " + dte)


if __name__ == "__main__":
    main()
