#!/usr/local/bin/python3

"""
Use Selenium package to extact the link to the Handsards from the North
Western Territories Parliament website.

"""

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select

import time
import re
import csv


def mth_convert(m_str):
    m_dic = {'jan': 1, 'january': 1, 'feb': 2, 'february': 2, 'mar': 3,
             'march': 3, 'apr': 4, 'april': 4, 'may': 5, 'jun': 6, 'june': 6,
             'jul': 7, 'july': 7, 'aug': 8, 'august': 8, 'sep': 9,
             'september': 9, 'oct': 10, 'october': 10, 'nov': 11,
             'november': 11, 'dec': 12, 'december': 12}
    if m_str.lower() not in m_dic.keys():
        return 0
    else:
        return (m_dic[m_str.lower()])


def hansard_lnks_to_csv(file_prefix, list_of_links):
    with open('NWT/'+file_prefix+'.csv', 'w') as f_out:
        writer = csv.writer(f_out, delimiter=',', quotechar='"',
                            quoting=csv.QUOTE_ALL)
        writer.writerow(['Assembly', 'Session', 'Date', 'Word', 'PDF'])
        # writer.writerows(list_of_links)
        for idx in range(len(list_of_links)):
            writer.writerow(list_of_links[idx].split(','))


def get_web_driver(driver_loc, web_loc):
    web_driver = webdriver.Chrome(executable_path=driver_loc)
    web_driver.get(web_loc)
    assert 'Hansard' in web_driver.title

    return web_driver


def get_nwt_assembly_links(web_driver):
    assembly_dict = {}
    for row in web_driver.find_elements_by_css_selector("table.cols-0"):
        session_dict = {}
        links = row.find_elements_by_tag_name('a')
        current_assembly = links[0].text
        current_session = ''
        # print('Row:', links[0].text)
        for count in range(1, len(links)):
            # print('\t', links[count].text, ':',
            #       links[count].get_attribute('href'))
            current_session = links[count].text
            lnk = links[count].get_attribute('href')
            session_dict[current_session] = lnk
        assembly_dict[current_assembly] = session_dict
    return assembly_dict


def main():
    path_to_driver = '/Users/curtishendricks/Development/indigenous-parliaments /indigenous-parliaments/chromedriver'
    site = 'https://www.ntassembly.ca/documents-proceedings/hansard'

    driver = get_web_driver(path_to_driver, site)

    assembly_links = get_nwt_assembly_links(driver)
    driver.close()

    doc_links = []
    for assembly_name in assembly_links.keys():
        assembly = assembly_links[assembly_name]
        for session_name in assembly.keys():
            driver = get_web_driver(path_to_driver, assembly[session_name])
            for table in driver.find_elements_by_css_selector('.cols-4'):
                captions = table.find_elements_by_tag_name('caption')
                rows = table.find_elements_by_tag_name('tr')
                for row in rows:
                    row_string = ''
                    row_string += captions[0].text + ','
                    txt_words = row.text.split()
                    len_words = len(txt_words)
                    if len_words > 2:
                        mth_str = mth_convert(txt_words[2])
                        dte_str = '-'.join([str(txt_words[4]), str(mth_str),
                                            txt_words[3]])
                        row_string += dte_str
                        links = row.find_elements_by_tag_name('a')
                        if len(links) > 0:
                            href = links[0].get_attribute('href')
                            if links[0].text == 'Word':
                                if '.docx' in href:
                                    row_string += href
                            row_string += ','
                            if links[0].text == 'PDF':
                                row_string += href
                            if 1 < len(links):
                                href = links[1].get_attribute('href')
                                if '.pdf' in href:
                                    row_string += href
                        doc_links.append(row_string)
            driver.close()

    hansard_lnks_to_csv('nwt_hansards', doc_links)

    for line in doc_links:
        print(line)


if __name__ == '__main__':
    main()
