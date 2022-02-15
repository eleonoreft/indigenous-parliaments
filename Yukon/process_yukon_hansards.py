#!/usr/local/bin/python3

import csv
import requests

import process_pdfs as procpdf

from weasyprint import HTML

from indig_parl_logger import get_logger
from indig_parl_utils import download_mht, send_text_to_file
from indig_parl_re import text_rem_patterns, text_extract_pattern
from process_mhts import extract_files

Yukon_logger = get_logger("Process_Yukon_Hansards",
                          a_log_file='Yukon/logs/proc_yukon_debug.log')


def get_csv_links(csv_pth, columns, line_zero=False):
    """Reads a csv file located in "csv_pth" and creates a list of dictionaries
    where each item in the list is a dictionary representing a line in the CSV
    file. The keys for the dictionary are the column names given in the list
    "columns"

    Arguments:
        csv_pth {[type]} -- [description]
        columns {[type]} -- [description]

    Returns:
        [type] -- [description]
    """
    lines = []
    title = 0
    with open(csv_pth, newline='') as csv_f:
        csv_reader = csv.reader(csv_f, delimiter=',', quotechar='"')
        for row in csv_reader:
            if title == 0 and not line_zero:
                title += 1
            else:
                row_dict = {}
                for col_idx in range(len(columns)):
                    row_dict[columns[col_idx].lower()] = row[col_idx]
                lines.append(row_dict)
    return lines


def process_converted_pdfs(pdf_path, str_date, file_prefix):

    # title_patterns = [r'Yukon Legislative Assembly', r'Page\s\d{1,4}',
    #                   r'[A-Z][a-z]+\s\d{1,2},\s\d{4}']
    # oral_sec_pattern = r'ITEM\s+\d{1,2}:\s+ORAL QUESTIONS\s*(.*?)\s*ITEM'
    oral_sec_pattern = r'QUESTION PERIOD(.*)?Question Period has now elapsed'
    quest_head_pattern = r'(Question\s+\d{1,3}.*?:)(.*?)(M[R|S]S{0,1}\.|HON\.|HONOURABLE)'
    speaker_pattern = r'((?:M[R|S]S{0,1}\.|HON\.|HONOURABLE).*?):'

    sec_head = 'QUESTION PERIOD'

    try:
        pdf_text = procpdf.pdf_to_text(pdf_path)
        Yukon_logger.debug('Got pdf_text from %s' % pdf_path)
        send_text_to_file('Yukon/tmp/'+str_date+'pdf_text.txt', pdf_text)
        # flat_text = text_rem_patterns(pdf_text, title_patterns + ['\n'])
        flat_text = text_rem_patterns(pdf_text, ['\n'])

        if sec_head in flat_text:
            print('(|)')
            Yukon_logger.debug('ORAL QUESTION FOUND in %s' % pdf_path)
            send_text_to_file('Yukon/tmp/'+str_date+'flat_text.txt',
                              flat_text)
            oral_q_section = text_extract_pattern(flat_text,
                                                  oral_sec_pattern)
            send_text_to_file('Yukon/tmp/'+str_date+'oral_q_sec.txt',
                              oral_q_section.group(1))

            csv_name = 'Yukon/csvs/' + file_prefix + str_date + '.csv'
            procpdf.process_pdf_oral_q(oral_q_section.group(1),
                                       quest_head_pattern, speaker_pattern,
                                       csv_name, str_date)
        else:
            print('(-)')
            Yukon_logger.debug('ORAL QUESTION NOT found in %s' % pdf_path)
    except Exception as e:
        print('(-)')
        Yukon_logger.debug(
            'Error extracting text from %s. Exception %s' % (pdf_path, e))


def main():
    # download handsards and store to locations to dictionaries
    # process the types of files
    csv_tst_file = 'Yukon/yukon_hansards.csv'
    csv_cols = ["Date_Long", "Date_Short", "MHT", "PDF"]
    tst_lst = get_csv_links(csv_tst_file, csv_cols)

    for idx in range(10):
        print(idx, ': ', tst_lst[idx]['mht'])
        output_file = download_mht(tst_lst[idx]['mht'],
                                   tst_lst[idx]["date_short"],
                                   directory='Yukon/mhts/')
        print('\t:', output_file)
        outcome = extract_files(output_file)
        if outcome:
            print('HTML conversion successful')
            html_file = HTML(outcome)
            pdf_name = output_file.split('/')[-1:][0].split('.')[0]
            pdf_path = 'Yukon/pdfs/'+pdf_name+'.pdf'
            html_file.write_pdf(pdf_path)
            print('Saved to pdf:', pdf_path)
            process_converted_pdfs(pdf_path, tst_lst[idx]["date_short"], '')
        else:
            print('HTML conversion successful')

        # html_file = HTML(output_file)
        # html_file.write_pdf('Yukon/pdfs/'+str(idx)+'.pdf')


if __name__ == '__main__':
    main()
