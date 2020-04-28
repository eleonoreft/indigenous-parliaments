#!/usr/local/bin/python3

"""
Use Selenium package to extact the link to the Handsards from the Nunavut
Parliament website.

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


def get_main_finals(web_driver):

    pat1 = re.compile(r'(\d{8})')

    final_xp = '//*[@id="quicktabs-tab-1-1"]'
    web_driver.find_element_by_xpath(final_xp).click()
    final_lnks = {}
    other_lnks = []
    # final_names = {}
    while True:
        for counter in range(1, 11):
            sp_st = '//*[@id="quicktabs_tabpage_1_1"]/div/div/table/tbody/tr['
            sp_ed = ']/td/span/span/a'
            sp = sp_st + str(counter) + sp_ed
            try:
                pth = web_driver.find_element_by_xpath(
                    sp).get_attribute('href')
                match1 = pat1.search(pth)
                if match1:
                    ky = match1.group(1)
                    final_lnks[ky] = pth
                else:
                    ky = None
                    other_lnks.append(pth)
                # print('\tPDF name: %s' % nme)
                print('-|', end='')
            except:
                # print("Link %s not present." % counter)
                break

        try:
            next_link = web_driver.find_element_by_partial_link_text("next")
            # print("Link:", next_link.get_attribute('href'))
            print()
            next_link.click()
            # need to give time for loading of content
            time.sleep(1)
        except:
            print('\nFinals Completed...')
            break

    return final_lnks, other_lnks


def main_final_to_csv(file_prefix, finals_dict, session):
    with open(file_prefix + '.csv', 'w') as f_out:
        writer = csv.writer(f_out, delimiter=',', quotechar='"',
                            quoting=csv.QUOTE_ALL)
        writer.writerow(['Session', 'Session Date', 'Session Link'])
        for dte in finals_dict.keys():
            writer.writerow([session, dte, finals_dict[dte]])


def get_archive_session_names(web_driver, lst_xp):
    dp_lst = Select(web_driver.find_element_by_xpath(lst_xp))
    names = []
    for o in dp_lst.options:
        if o.text[:1] != '<':
            names.append(o.text)
    print('Session names collected.')
    return names


def get_session_links(web_driver):
    archive_lnks = {}
    other_lnks = []
    pat1 = re.compile(r'(\d{8})')
    pat2 = re.compile(r'/([a-z,A-Z]*)\s*(\d\d)\s*,\s*([1,2][0,9]\d\d).')

    while True:
        for tab in [1, 2]:
            xp_st_1 = '/html/body/div[1]/div[4]/div[2]/div/div[2]/div[2]/div/div/div/div/div/div/div/div/div[3]/table['
            xp_st_2 = ']/tbody/tr['
            xp_ed = ']/td/span/span/a'
            print()
            for row in range(1, 11):
                xpath = xp_st_1 + str(tab) + xp_st_2 + str(row) + xp_ed
                try:
                    pth = web_driver.find_element_by_xpath(
                        xpath).get_attribute('href')
                    match1 = pat1.search(pth)
                    match2 = pat2.search(re.sub('%20', ' ', pth))
                    if match1:
                        ky = match1.group(1)
                        archive_lnks[ky] = pth
                    elif match2:
                        m_num = mth_convert(match2.group(1))
                        d_str = match2.group(3) + match2.group(2) + str(m_num)
                        ky = d_str
                        archive_lnks[ky] = pth
                    else:
                        ky = None
                        other_lnks.append(pth)
                    print('-|', end='')
                    # print('\tPDF path: %s, key: %s' % (pth, ky))
                except:  # Exception as e:
                    # print('EXCEPTION >>>', e)
                    # print('Except table:%s, row: %s' % (tab, row))
                    continue
        for row in range(1, 11):
            xp_st = '/html/body/div[1]/div[4]/div[2]/div/div[2]/div[2]/div/div/div/div/div/div/div/div/div[3]/table/tbody/tr['
            xp_ed = ']/td/span/span/a'
            xpath = xp_st + str(row) + xp_ed
            try:
                pth = web_driver.find_element_by_xpath(
                    xpath).get_attribute('href')
                match1 = pat1.search(pth)
                match2 = pat2.search(re.sub('%20', ' ', pth))
                if match1:
                    ky = match1.group(1)
                    archive_lnks[ky] = pth
                elif match2:
                    m_num = mth_convert(match2.group(1))
                    d_str = match2.group(3) + match2.group(2) + str(m_num)
                    ky = d_str
                    archive_lnks[ky] = pth
                else:
                    ky = None
                    other_lnks.append(pth)
                print('-|', end='')
                # print('\tPDF path: %s, key: %s' % (pth, ky))
            except:  # Exception as e:
                # print('EXCEPTION >>>', e)
                # print('Except row:', row)
                continue
        try:
            nxt_btn = web_driver.find_elements_by_partial_link_text('next')
            nxt_btn[1].click()
            print()
            time.sleep(1)
        except:
            print('\nArchived Session Finals Completed...')
            break

    return archive_lnks, other_lnks


def write_archives_to_csv(file_prefix, archive_dict):
    with open(file_prefix + '.csv', 'w') as f_out:
        writer = csv.writer(f_out, delimiter=',', quotechar='"',
                            quoting=csv.QUOTE_ALL)
        writer.writerow(['Session', 'Session Date', 'Session Link'])
        for session in archive_dict.keys():
            session_dict = archive_dict[session]
            for dte in session_dict.keys():
                writer.writerow([session, dte, session_dict[dte]])


def list_to_txt_file(file_prefix, out_list):
    with open(file_prefix + '.txt', 'w') as f_out:
        for line in out_list:
            f_out.write(line + '\n')


def get_session_archives(web_driver, lst_xp, app_btn_xp):
    archive = {}
    unknown = []
    for name in get_archive_session_names(web_driver, lst_xp):
        dp_lst = Select(web_driver.find_element_by_xpath(lst_xp))
        dp_lst.select_by_visible_text(name)
        try:
            web_driver.find_element_by_xpath(app_btn_xp).click()
            print('Applied session', name, end='. ')
            time.sleep(1)
            archive_session, unknown_items = get_session_links(web_driver)
            archive[name] = archive_session
            unknown += unknown_items
        except Exception as e:
            print(e)

    return archive, unknown


def csv_2_date_path_dict(in_file, key_field="Session Date",
                         value_field="Session Link"):
    csv_dict = {}
    with open(in_file, 'r') as csv_in:
        csv_reader = csv.DictReader(csv_in)
        for row in csv_reader:
            ky = row[key_field]
            vl = row[value_field]
            csv_dict[ky] = vl
    return csv_dict


def get_web_driver(driver_loc, web_loc):
    web_driver = webdriver.Chrome(executable_path=driver_loc)
    web_driver.get(web_loc)
    assert 'Hansard' in web_driver.title

    return web_driver


def main():
    path_to_driver = '/Users/curtishendricks/Development/indigenous-parliaments /indigenous-parliaments/chromedriver'
    site = 'https://assembly.nu.ca/hansard'

    driver = get_web_driver(path_to_driver, site)
    time.sleep(1)

    # Get current data
    current_final_links, other = get_main_finals(driver)
    driver.close()

    main_final_to_csv('5-Assembly', current_final_links, '5th Assembly')
    if other:
        list_to_txt_file('5-Ass-unknown', other)

    print('FINALS')
    print('Total current finals:', len(current_final_links.keys()))
    if other:
        print('Other links:', len(other))
        for lnk in other:
            print('\t', lnk, end='')
        print()

    driver = get_web_driver(path_to_driver, site)
    time.sleep(1)

    # Get archive data

    list_xp = '//*[@id="edit-tid-1"]'
    apply_btn_xp = '//*[@id="edit-submit-hansard-archive"]'
    archives, unknowns = get_session_archives(driver, list_xp, apply_btn_xp)
    driver.close()

    write_archives_to_csv('archives', archives)
    if unknowns:
        list_to_txt_file('unknown_files', unknowns)

    print('ARCHIVES')
    count = 0
    for archive_name in archives.keys():
        print(archive_name, ':', end=' ')
        paths = archives[archive_name]
        sub_count = 0
        for _ in paths.keys():
            sub_count += 1
        print(sub_count)
        count += sub_count
    print('Total:', count)
    print('Unknown total:', len(unknowns))


if __name__ == '__main__':
    main()
