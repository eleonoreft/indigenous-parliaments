#!/usr/local/bin/python3

import csv
import os

import process_pdfs as procpdf

from weasyprint import HTML

from indig_parl_logger import get_logger
from indig_parl_utils import download_pdf, send_text_to_file
from indig_parl_re import text_rem_patterns, text_extract_pattern

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


def process_pdfs(pdf_path, str_date, file_prefix):

    # Regex pattern for extracting the entire 'Question Period' section from the Hansard
    oral_sec_pattern = 'QUESTION PERIOD(.*)?\s*(?:The\s+){0,1}[T|t]ime\s+for\s+Question\s+Period'
    # Regex pattern for splitting the 'Question Period' section into the various subsections with the discussion related to each question
    quest_head_pattern = r'Question re:'
    # Regex pattern to pull out the names/titles of the persons discussing the questions from the 'Question Period' section
    speaker_pattern = r'((?:Hon\.\s){0,1}(?:Honourable\.\s){0,1}M[r|s]s{0,1}\.\s((?!Speaker).)*?:)'
    sec_head = 'QUESTION PERIOD' # String to identify if required section is in the document
    try:
        pdf_text = procpdf.pdf_to_text(pdf_path)
        Yukon_logger.debug('Got pdf_text from %s' % pdf_path)
        send_text_to_file('Yukon/tmp/'+str_date+'[0]-pdf_text.txt', pdf_text)
        flat_text = text_rem_patterns(pdf_text, ['\n'])

        if sec_head in flat_text:
            print('(|)')
            Yukon_logger.debug('ORAL QUESTION FOUND in %s' % pdf_path)
            send_text_to_file('Yukon/tmp/'+str_date+'[1]-flat_text.txt',
                              flat_text)
            oral_q_section = text_extract_pattern(flat_text,
                                                  oral_sec_pattern)
            send_text_to_file('Yukon/tmp/'+str_date+'[2]-oral_q_sec.txt',
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
    yukon_hansard_lnks = 'Yukon/yukon_hansards.csv'
    csv_cols = ["Date_Long", "Date_Short", "MHT", "PDF"]
    lst_hansard_lnks = get_csv_links(yukon_hansard_lnks, csv_cols)

    # # Download PDFs
    # # count = 0   # To limit the number of pdfs downloaded
    # for line in lst_hansard_lnks:
    #     # count += 1
    #     print(line['pdf'])
    #     download_pdf(line['pdf'], line['date_short'], directory='Yukon/pdfs/')
    #     # if count == 20: # The max number of pdfs to download
    #     #     break
    
    # Process PDFs
    pdf_file_loc = 'Yukon/pdfs/2020s/'
    pdf_dir = os.listdir(pdf_file_loc)
    # count = 0   # To limit the number of pdfs to process
    for file in pdf_dir:
        if os.path.isfile(os.path.join(pdf_file_loc, file)) and file.endswith('.pdf'):
            # count += 1
            # print(f' >> {file}. Date: {file[1:11]} ')
            dte_string = file[1:11]
            prefix = ''
            process_pdfs(pdf_file_loc+file, dte_string, prefix)
        # if count == 50: # The max number of pdfs to process
        #     break


if __name__ == '__main__':
    main()
