#!/usr/local/bin/python3
# coding: utf-8
import sys
import re
import requests
import pandas as pd
import textract
import datetime

import time

from selenium import webdriver
from selenium.webdriver.common.keys import Keys


# Collect main Fifth Assembly Finals
def get_main_finals():

    path_to_driver = '/Users/curtishendricks/web-driver/chromedriver'
    driver = webdriver.Chrome(executable_path=path_to_driver)
    driver.get('https://assembly.nu.ca/hansard')
    assert 'Hansard' in driver.title

    final_xp = '//*[@id="quicktabs-tab-1-1"]'
    driver.find_element_by_xpath(final_xp).click()
    final_lnks = {}
    final_names = {}
    while True:
        for counter in range(1, 11):
            sp_st = '//*[@id="quicktabs_tabpage_1_1"]/div/div/table/tbody/tr['
            sp_ed = ']/td/span/span/a'
            sp = sp_st + str(counter) + sp_ed
            try:
                pth = driver.find_element_by_xpath(sp).get_attribute('href')
                [nme] = pth.split('/')[-1:]
                ky = nme[:8]
                final_lnks[ky] = pth
                final_names[ky] = nme
                print('\tPDF name: %s' % nme)
            except:
                print("Link %s not present." % counter)
                break

        try:
            next_link = driver.find_element_by_partial_link_text("next")
            print("Link:", next_link.get_attribute('href'))
            next_link.click()
            # need to give time for loading of content
            time.sleep(2)
        except:
            print('Finals Completed...')
            break

    return final_lnks, final_names


def get_pdf(date):
    # sometimes the files have a "_0" associated with them
    #url = "http://www.assembly.nu.ca/sites/default/files/" \
    #   + date + "-Blues-English.pdf"
    #url = "http://www.assembly.nu.ca/sites/default/files/" \
    #   + date + "_Final.pdf"
    url = "http://www.assembly.nu.ca/sites/default/files/Hansard_" + date \
        + ".pdf"
    r = requests.get(url)
    file = "./pdfs/" + date + ".pdf"
    with open(file, 'wb') as f:
        f.write(r.content)
    return file


def extract_speakers(pdf, first_page):
    speaker_list = []
    print(first_page.find("Members Present"))
    st = first_page.find("Members Present")
    en = first_page.find("Item 1")
    page = first_page[st:en]
    page = page.replace("Members Present:", '').replace('.', '')
    page = page.replace("\n", " ")
    clean_page = page.split(", ")
    titles = ["Ms", "Mr", "Hon", "Honourable"]
    for _, v in enumerate(clean_page):
        speaker_list.append(v)
        speaker_words = v.split(" ")
        for t in titles:
            if t in v:
                speaker_list.append(
                    speaker_words[0] + " " + speaker_words[2].replace(".", ""))
            else:
                speaker_list.append(
                    t + " " + speaker_words[1].replace(".", ""))
    for speaker in speaker_list:
        if "Honourable" in speaker:
            speaker_list.append(speaker.replace("Honourable", "Hon"))
    return speaker_list


def process_pdf(pdf, date):
    clean_page = textract.process(pdf)
    clean_df = pd.DataFrame(columns=["speaker", "speech"])
    speaker_list = None
    speaker_list = extract_speakers(pdf, clean_page)
    print(speaker_list)
    speaker_list.append("Question")
    print(speaker_list)
    clean_page = clean_page[clean_page.find("Opening Prayer"):]
    clean_page = clean_page.replace("Thank you, Mr. Speaker.", "")
    clean_page = clean_page.replace("Thank you, Mr. Chairman.", "")
    clean_page = clean_page.replace(">>Applause", "")
    clean_page = clean_page.replace(">>Laughter", "")
    clean_page = clean_page.replace("\n", " ")
    clean_page = clean_page.replace(" (interpretation)", "")
    clean_page = clean_page.replace("(interpretation ends)", "")
    clean_page = clean_page.replace("Nunavut Hansard ", "")
    clean_page = clean_page.replace("“", "")
    clean_page = clean_page.replace(".", "")
    clean_page = clean_page.replace(",", "")
    clean_page = clean_page.decode('utf-8').encode('ascii', errors='ignore')
    # Strip date from header
    date = str(date)
    year = int(date[:4])
    month = int(date[4:6])
    day = int(date[6:8])
    hansard_date = datetime.datetime(year, month, day)
    pg_st = clean_page.find("Item 6: Oral Questions")
    pg_en = clean_page.find("the time for question period has expired")
    clean_page = clean_page[pg_st:pg_en]
    date_string = hansard_date.strftime("%A, %B %-d, %Y")
    clean_page = clean_page.replace(date_string, "")
    clean_page = re.sub(
        r'[a-zA-Z]+\s[a-zA-Z]+\s[0-9]{1,2}\s2[0-9]{3}\s{1,3}[0-9]{1,2}',
        ' ', clean_page)
    for s in speaker_list:
        clean_page = clean_page.replace(s+":", s+":**")
    clean_page = clean_page.replace("Speaker:", "Speaker:**")
    clean_page = clean_page.replace("Chairman:", "**Chairman:**")
    clean_page = clean_page.split("**")
    for k, v in enumerate(clean_page):
        for t in speaker_list:
            if t+":" in v:
                try:
                    df = pd.DataFrame(
                        data={"speaker": [t], "speech": [clean_page[k+1]]})
                    clean_df = clean_df.append(df, ignore_index=True)
                except IndexError:
                    print(v)
    clean_df['speech'] = clean_df['speech'].apply(
        lambda x: x.replace("Speaker:", ""))
    print(clean_df)
    return clean_df


def main(date=sys.argv[1]):
    # Add a loop for this to check and add for files automatically
    # python get_nunavut_hansards.py 20010321
    # Link to pdfs: https://assembly.nu.ca/hansard
    # Problem 1: get all the pdfs from beginning of time
    #   (Nunavut creation 1999)
    # Problem 2: some speeches are getting cropped (examples to come)
    pdf_name = get_pdf(date)
    hansard_df = process_pdf(pdf_name, date)
    hansard_df.to_csv("./clean_csvs/"+date+".csv", encoding='utf-8-sig')
    print("CSV saved for: " + date)


if __name__ == '__main__':
    main()
