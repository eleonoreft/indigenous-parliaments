#!/usr/local/bin/python3

import csv
import requests
# import docx

from weasyprint import HTML

from indig_parl_logger import get_logger
from indig_parl_utils import download_mht
from process_mhts import extract_files
# from process_docs import get_doc_obj_txt

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


# def download_mht(web_loc, date, directory="mhts/"):
#     """Downloads a MHT file form webaddress 'web_loc' and saves it to location
#     'directory'

#     Arguments:
#         web_loc {[type]} -- [description]
#         date {[type]} -- [description]

#     Keyword Arguments:
#         directory {str} -- [description] (default: {"pdfs/"})

#     Returns:
#         string -- path to downloaded file
#     """
#     [name] = web_loc.split('/')[-1:]
#     r = requests.get(web_loc)
#     file_loc = directory+"["+date+"]"+name
#     with open(file_loc, 'wb') as f:
#         f.write(r.content)
#     return file_loc


def download_hansards(csv_pth, columns, to_get):
    '''
    Open csv file in "csv_pth" with column headers in list "columns" and
    download the files to the required folders. The "to_get" list entries store
    [{File store location}, {Column with file link}, {return dictionary 
    key:value pair}]
    e.g.: 
    columns = ["Date_Long", "Date_Short", "MHT", "PDF"]
    to_get = {['Yukon/mhts/', 'MHT', ['Date_Short','MHT']], 
              ['Yukon/pdfs/', 'PDF', ['Date_short','PDF']]}
    '''
    pass


def main():
    # download handsards and store to locations to dictionaries
    # process the types of files
    csv_tst_file = 'Yukon/yukon_hansards.csv'
    csv_cols = ["Date_Long", "Date_Short", "MHT", "PDF"]
    tst_lst = get_csv_links(csv_tst_file, csv_cols)

    for idx in range(10):
        print(idx, ': ', tst_lst[idx]['mht'])
        output_file = download_mht(tst_lst[idx]['mht'], "date_short",
                                   directory='Yukon/mhts/')
        print('\t:', output_file)
        outcome = extract_files(output_file)
        if outcome:
            print('HTML conversion successful')
            html_file = HTML(outcome)
            pdf_name = output_file.split('/')[-1:][0].split('.')[0]
            html_file.write_pdf('Yukon/pdfs/'+pdf_name+'.pdf')
            print('Saved to pdf: Yukon/pdfs/'+pdf_name+'.pdf')
        else:
            print('HTML conversion successful')

        # html_file = HTML(output_file)
        # html_file.write_pdf('Yukon/pdfs/'+str(idx)+'.pdf')


if __name__ == '__main__':
    main()
