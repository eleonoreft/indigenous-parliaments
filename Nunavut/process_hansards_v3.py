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
    re_pg_header = r'\s[A-Z][a-z]+,{0,1}\s[A-Z][a-z]+\s\d{1,2},\s[1,2][0,9]\d{2}\s+Nunavut Hansard'
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
    q_titles = r'\s*(Question\s+\d{1,3}\s*\S\s\d\(\d\)):'
    # speaker_headers = r'\s*((?:M[r|s]s{0,1}\.|Hon\.|Honourable|Speaker)(?:\s+[A-Z]\w+?\.{0,1}){0,2})\s*(?:\(\w+\))?:'
    # speaker_headers = r'\s*((?:M[r|s]s{0,1}\.|Hon\.|Honourable|Speaker)(?:\s+(?:O\S){0,1}[A-Z]\w+?\.{0,1}){0,2})\s*(?:\(\w+\)){0,1}:'
    speaker_headers = r'\s*((?:M[r|s]s{0,1}\.{0,1}|Hon\.{0,1}|Honourable|Speaker)(?:\s+(?:O\S){0,1}[A-Z]\w+?\.{0,1}){0,2})\s*(?:\(\w+\)){0,1}:'

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
        send_text_to_file('Nunavut/clean_csvs/'+d_str +
                          'pre_q_split_raw.txt', q_list, data_type='list')
        for idx in range(len(q_list)):
            if not 'Question' == q_list[idx][:8]:
                speaker_pattern = re.compile(speaker_headers)
                speaker_match = speaker_pattern.search(q_list[idx])
                if speaker_match:
                    (start, _) = speaker_match.span()
                    q_tail = q_list[idx][:start]
                    print('Question tail:', q_tail)
                    dialog = q_list[idx][start:]
                    print('Old question:', q_list[idx-1])
                    q_list[idx-1] += ': ' + q_tail
                    print('New question:', q_list[idx-1])
                    q_list[idx] = dialog

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
            even_diag_list = diag_list[1::2]
            odd_diag_list = diag_list[::2]
            diag_tup_list = list(zip(odd_diag_list, even_diag_list))
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


def main():
    # path_dct = csv_2_date_path_dict('Nunavut/5-Assembly.csv')
    # path_dct = csv_2_date_path_dict('Nunavut/special_file.csv')
    # path_dct = csv_2_date_path_dict('Nunavut/archives.csv')
    # path_dct = csv_2_date_path_dict('Nunavut/archives_4th.csv')
    # path_dct = csv_2_date_path_dict('Nunavut/archives_3rd.csv')
    # path_dct = csv_2_date_path_dict('Nunavut/archives_2nd.csv')
    path_dct = csv_2_date_path_dict('Nunavut/archives_1st.csv')
    for dte in path_dct:
        pdf_name = get_pdf(path_dct[dte], dte)
        hansard_df = process_pdf(pdf_name, dte)
        if not hansard_df.empty:
            hansard_df.to_csv("Nunavut/clean_csvs/"+dte +
                              ".csv", encoding='utf-8-sig')
            print("CSV saved for: " + dte)


if __name__ == "__main__":
    main()
