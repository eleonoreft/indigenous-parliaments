#!/usr/local/bin/python3

import indig_parl_utils as utils
import process_pdfs as procpdf
import process_docs as procdoc

from indig_parl_re import text_rem_patterns, text_extract_pattern
from indig_parl_logger import get_logger


nwt_logger = get_logger("Process_NWT_Hansards",
                        a_log_file='NWT/logs/proc_nwt_debug.log')


def process_docs(doc_path, assembly_name):
    oral_q_doc = procdoc.get_oral_q_doc_obj(doc_path)
    if not oral_q_doc == None:
        print('(|)')
        nwt_logger.debug('ORAL QUESTION FOUND in %s' % doc_path)
        procdoc.process_doc_oral_q(oral_q_doc, doc_path, assembly_name)
    else:
        print('(-)')
        nwt_logger.debug('ORAL QUESTION NOT found in %s' % doc_path)
    nwt_logger.debug('Document path: %s' % doc_path)


def process_pdfs(pdf_path, str_date, file_prefix):

    title_patterns = [r'NORTHWEST TERRITORIES HANSARD', r'Page\s\d{1,4}',
                      r'[A-Z][a-z]+\s\d{1,2},\s\d{4}']
    oral_sec_pattern = r'ITEM\s+\d{1,2}:\s+ORAL QUESTIONS\s*(.*?)\s*ITEM'
    quest_head_pattern = r'(Question\s+\d{1,3}.*?:)(.*?)(M[R|S]S{0,1}\.|HON\.|HONOURABLE)'
    speaker_pattern = r'((?:M[R|S]S{0,1}\.|HON\.|HONOURABLE).*?):'

    sec_head = 'ORAL QUESTIONS'

    try:
        pdf_text = procpdf.pdf_to_text(pdf_path)
        utils.send_text_to_file('NWT/tmp/'+str_date+'pdf_text.txt', pdf_text)
        flat_text = text_rem_patterns(pdf_text,
                                      title_patterns + ['\n'])

        if sec_head in flat_text:
            print('(|)')
            nwt_logger.debug('ORAL QUESTION FOUND in %s' % pdf_path)
            utils.send_text_to_file('NWT/tmp/'+str_date+'flat_text.txt',
                                    flat_text)
            oral_q_section = text_extract_pattern(flat_text,
                                                  oral_sec_pattern)
            utils.send_text_to_file('NWT/tmp/'+str_date+'oral_q_sec.txt',
                                    oral_q_section.group(1))

            csv_name = 'NWT/csvs/' + file_prefix + str_date + '.csv'
            procpdf.process_pdf_oral_q(oral_q_section.group(1),
                                       quest_head_pattern, speaker_pattern,
                                       csv_name, str_date)
        else:
            print('(-)')
            nwt_logger.debug('ORAL QUESTION NOT found in %s' % pdf_path)
    except Exception as e:
        print('(-)')
        nwt_logger.debug(
            'Error extracting text from %s. Exception %s' % (pdf_path, e))


def main():
    #logging.basicConfig(filename='NWT/proc_nwt_debug.log', level=logging.DEBUG)

    # hansard_csv = 'NWT/nwt_hansards_small_assem.csv'
    hansard_csv = 'NWT/nwt_hansards_19_assem.csv'
    # hansard_csv = 'NWT/nwt_hansards_18_assem.csv'
    # hansard_csv = 'NWT/nwt_hansards_17_assem.csv'
    # hansard_csv = 'NWT/nwt_hansards_16_assem.csv'
    # hansard_csv = 'NWT/nwt_hansards_15_assem.csv'
    # hansard_csv = 'NWT/nwt_hansards_14_assem.csv'

    docx_paths, pdf_paths = utils.download_hansards(hansard_csv,
                                                    doc_dir="NWT/docs/",
                                                    pdf_dir="NWT/pdfs/")

    print('Processing Hansards ')
    if len(docx_paths.keys()) > 0:
        nwt_logger.debug('Processing %s ".docx" hansards.' %
                         len(docx_paths.keys()))
    for key in docx_paths.keys():
        path = docx_paths[key][2]
        if path:
            process_docs(path, docx_paths[key][0])
        else:
            print('(-)')
            nwt_logger.debug('Empty DOCX path for %s' % docx_paths[key][0] +
                             ', ' + docx_paths[key][1] + ',' +
                             docx_paths[key][2])
    if len(pdf_paths.keys()) > 0:
        nwt_logger.debug('Processing %s ".pdf" hansards.' %
                         len(pdf_paths.keys()))
    for key in pdf_paths.keys():
        path = pdf_paths[key][2]
        dte = path.split('/')[-1:][0][1:11]
        prefix = pdf_paths[key][0]
        if path:
            process_pdfs(path, dte, prefix)
        else:
            print('(-)')
            nwt_logger.debug('Empty PDF path for %s' % prefix + ',' +
                             pdf_paths[key][2])

    print('Extracted Oral Questions in folder "NWT/csvs/"')


if __name__ == "__main__":
    main()
