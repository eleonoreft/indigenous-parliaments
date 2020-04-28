#!/usr/local/bin/python3

import textract

import re
import requests
import pandas as pd

from nunavut_hansards import csv_2_date_path_dict


def get_pdf(url, dte_str):
    r = requests.get(url)
    file_loc = "Nunavut/pdfs/" + dte_str + ".pdf"
    with open(file_loc, 'wb') as f:
        f.write(r.content)
    return file_loc


def speaker_from_variation(speaker_dict, variation):
    for speaker in speaker_dict.keys():
        speaker_vars = speaker_dict[speaker]
        if variation.lower() in [person.lower() for person in speaker_vars]:
            return speaker
    else:
        return None


def get_speakers(raw_text):
    # Pattern: concatenated first and last names that are capitalized
    cap_name_pat = re.compile(r'([A-Z][a-z]+)([A-Z][a-z]+)')

    speakers_dict = {}
    speaker_lst = [speaker.strip() for speaker in raw_text.split(',')]
    for speaker in speaker_lst:
        full_lst = []
        names = speaker.split()
        # print('Name:', names[0], end=' ')
        name_split = names[0].split('.')
        if len(name_split) > 1 and not name_split[1] == '':
            new_names = []
            new_names.append(name_split[0] + '.')
            new_names.append(name_split[1])
            for count in range(1, len(names)):
                new_names.append(names[count])
            names = new_names
        #     print('NAMES:', names)
        # else:
        #     print()

        # check concatenated names
        if len(names) >= 2:
            cat_name_match = cap_name_pat.search(names[1])
            if cat_name_match:
                new_names = []
                new_names.append(names[0])
                new_names.append(cat_name_match.group(1))
                new_names.append(cat_name_match.group(2))
                for count in range(2, len(names)):
                    new_names.append(names[count])
                names = new_names
        if len(names) > 2:  # Assuming no names longer than 3 words
            full_lst.append(names[0] + ' ' + names[1] + ' ' + names[2])
            full_lst.append(names[0] + ' ' + names[2])
            full_lst.append(names[0] + ' ' + names[1])
            full_lst.append(names[1] + ' ' + names[2])
            full_lst.append(names[2])
            if names[0] == 'Hon.':
                full_lst.append('Honourable ' + names[1] + ' ' + names[2])
                full_lst.append('Honourable ' + names[2])
                full_lst.append('Honourable ' + names[1])
            if names[0] == 'Honourable':
                full_lst.append('Hon. ' + names[1] + ' ' + names[2])
                full_lst.append('Hon. ' + names[2])
                full_lst.append('Hon. ' + names[1])
        else:
            full_lst.append(speaker)
        # If orignal speaker has title concatinated with first name and/or
        # first and second name concatenated, it will replace the name with
        # the correct spacing between words
        speakers_dict[full_lst[0]] = full_lst
    return speakers_dict


def remove_phrases(phrase_dict, raw_text):
    for phrase in phrase_dict.keys():
        # print('TYPE(raw_text) in remove_phrases:', type(raw_text))
        raw_text = raw_text.replace(phrase, phrase_dict[phrase])
    return raw_text


def extract_oral_questions(raw_text):
    # question_pattern = re.compile(
    #     r'Item 6: Oral Questions(.*)the time (?:\w+\s){0,1}\s{0,1}for question period has expired')
    question_strings = [
        r'Item 6: Oral Questions(.*)question period has expired',
        r'Item 6: Oral Questions(.*)Question Period is now over',
        r'Item 6: Oral Questions(.*) Item 7: Written Questions',
        r'Item 6: Oral Questions(.*) Item 13: Tabling of Documents',
        r'Item 6: Oral Questions(.*) Thank you\. Oral Questions\. I have no more names on my list\.',
        r'Item 6: Oral Questions(.*)Item 18: First Reading of Bills',
        r'Item 6: Oral Questions(.*)Item 5: Recognition of Visitors',
        r'Item 6: Oral Questions(.*)Item 11: Reports of Standing',
        r'Item 6: Oral Questions(.*)Item 14: Tabling of Documents',
        r'Item 6: Oral Questions(.*) the time for question period has expired',
        r'Item 6: Oral Questions(.*) Item 13: Reports of Standing ',
        r'Item 6: Oral Questions(.*) time allotted for this item has expired',
        r'Item 6: Oral Questions(.*)Item 22: Orders of the Day'
        r'Item 6: Oral Questions(.*) the allotted time for question period has run out',
        r'Item 6: Oral Questions(.*) Item 19: Consideration in Committee',
        r'Item 6: Oral Questions(.*) the time for question period is expired'
    ]
    for count, pattern_string in enumerate(question_strings, 1):
        pattern = re.compile(pattern_string)
        pattern_match = pattern.search(raw_text)
        if pattern_match:
            print('PATTERN %s matched.' % count)
            questions_txt = pattern_match.group(1)
            break

    return questions_txt


def process_pdf(pdf_file_name, dte):
    # RE for the page separators Date, Hansard name and Sheet Number
    re_pg_header = r'\s[A-Z][a-z]+,\s[A-Z][a-z]+\s\d{1,2},\s[1,2][0,9]\d{2}\s+Nunavut Hansard'
    re_pg_footer = r'\s+\s\d{2,4}\n'
    phrases = {"Thank you, Mr. Speaker.": "", "Thank you, Mr. Chairman.": "",
               ">>Applause": "", ">>Laughter": "", " (interpretation)": "",
               "(interpretation ends)": "", "Nunavut Hansard ": "", '“': '\“',
               '”': '\”'}
    # Pattern: Extract attendance section
    # attendance_pattern = re.compile(r'Members Present:(.*)>>House commenced')
    # attendance_pattern = re.compile(
    #     r'Members Present:(.*)?(?:>>House commenced|Item 1:)')
    # attendance_pattern = re.compile(
    #     r'Members Present:(.*)?>>House commenced|Item 1:')
    attendance_pattern = re.compile(
        r'Members Present:(.*)?(?:>>House commenced|Item 1:)')

    try:
        raw_page = textract.process(pdf_file_name)
        raw_page = raw_page.decode('utf-8')
        # with open('Nunavut/clean_csvs/'+dte+'-raw.txt', 'w') as f:
        #     f.write(raw_page)
        # Remove page headers/footers
        raw_page = re.sub(re_pg_header, ' ', raw_page)
        raw_page = re.sub(re_pg_footer, '\n', raw_page)
        with open('Nunavut/clean_csvs/'+dte+'-2raw.txt', 'w') as f:
            f.write(raw_page)

        if raw_page.find("Item 6: Oral Questions") > -1:
            # 1. Get attendance section
            # 2. Get list of speakers from attendance
            # 3. Extract the question/answer(q&a) portion (Item 6) of the document
            # 4. Remove unwated phrases form q&a
            print('>> Processing:', pdf_file_name)
            # 1.
            # print('TYPE(raw_page 1) in process_pdf:', type(raw_page))
            raw_text = raw_page.replace('\n', ' ')
            with open('Nunavut/clean_csvs/'+dte+'-raw_text.txt', 'w') as f:
                f.write(raw_text)
            attendance_match = attendance_pattern.search(raw_text)
            if attendance_match:
                attendance_txt = attendance_match.group(1)
                # print('ATTENDANCE:\n', attendance_txt)
                attendance_txt = remove_phrases(phrases, attendance_txt)
                # 2.
                speakers = get_speakers(attendance_txt)
                with open('Nunavut/clean_csvs/'+dte+'speakers.txt', 'w') as f:
                    for speaker in speakers.keys():
                        f.write(speaker + ':\n')
                        variations = speakers[speaker]
                        for variation in variations:
                            f.write('\t>> ' + variation + '\n')
            # 3.
            # print('TYPE(raw_page 2) in process_pdf:', type(raw_page))
            raw_text = raw_page.replace('\n', ' ')
            questions_txt = extract_oral_questions(raw_text)

            # section_st = raw_text.find("Item 6: Oral Questions")
            # section_ed = raw_text.find(
            #     "the time for question period has expired")
            # questions_txt = raw_text[section_st:section_ed]

            questions_txt = remove_phrases(phrases, questions_txt)
            # print('Length questions text (phrases removed):', len(questions_txt))
            # with open('Nunavut/clean_csvs/'+dte+'.txt', 'w') as f:
            #     f.write(questions_txt)
            # speaker_headers = r'(?:Hon\.|Mr\.|M[r]{0,1}s\.){0,1}\s*(?:[A-Z]\w+){0,1}\s*[A-Z]\w+:'
            # speaker_headers = r'((?:Hon\.|Mr\.|M[r]{0,1}s\.){0,1}\s*(?:[A-Z]\w+){0,1}\s*[A-Z]\w+:)'
            speaker_headers = r'((?:Honorable|Hon\.|Mr\.|M[r]{0,1}s\.){0,1}\s*(?:[A-Z]\w+){0,1}\s*[A-Z]\w+:)'
            split_txt = re.split(speaker_headers, questions_txt)
            with open('Nunavut/clean_csvs/'+dte+'-raw-split.txt', 'w') as f:
                for item in split_txt:
                    f.write(item+'\n')
            # Remove any text prior to first speaker in the list
            while True:
                last_char = split_txt[0].strip()[-1:]
                if last_char != ':':
                    split_txt.pop(0)
                else:
                    break

            speakers_list = []
            speech_list = []
            for item in split_txt:
                # if 'Item 6:' in item:
                #     # print('ITEM 6 header')
                #     continue
                # else:
                if item.strip()[-1:] == ':':
                    # print('TYPE(item) in process_pdf:', type(item))
                    speaker_var = item.strip().replace(':', '')
                    if speaker_var == 'Speaker':
                        speakers_list.append('Speaker')
                        # print('Speaker added')
                    else:
                        speaker = speaker_from_variation(
                            speakers, speaker_var)
                        if speaker:
                            # print('Item: %s - Speaker: %s' %
                            #       (speaker_var, speaker))
                            speakers_list.append(speaker)
                        else:
                            # print('Raw speaker used:', item)
                            speakers_list.append(item)
                else:
                    speech_list.append(item)
            print('Speakers list length - %s\nSpeech list length - %s' %
                  (len(speakers_list), len(speech_list)))
            combined = list(zip(speakers_list, speech_list))
            speech_df = pd.DataFrame(combined, columns=['speaker', 'speech'])
            print('Combined length:', len(combined))
            # speech_df.to_csv('Nunavut/clean_csvs/'+dte+'.csv', sep=',')
            # with open('Nunavut/clean_csvs/'+dte+'-split.txt', 'w') as f:
            #     for a in split_txt:
            #         f.write(a+'\n\n')
            return speech_df
        else:
            print('%s has no data to process.' % pdf_file_name)
            return pd.DataFrame(columns=['speaker', 'speech'])
    except Exception as e:
        print('ERROR: Error reading/accessing pdf document for %s. [%s].' %
              (dte, pdf_file_name))
        print(e)
        return pd.DataFrame(columns=['speaker', 'speech'])


def main():
    # count = 0
    # break_out = 5
    # path_dct = csv_2_date_path_dict('Nunavut/5-Assembly.csv')
    path_dct = csv_2_date_path_dict('Nunavut/special_file.csv')
    # path_dct = csv_2_date_path_dict('Nunavut/archives.csv')
    for dte in path_dct:
        pdf_name = get_pdf(path_dct[dte], dte)
        hansard_df = process_pdf(pdf_name, dte)
        if not hansard_df.empty:
            hansard_df.to_csv("Nunavut/clean_csvs/"+dte +
                              ".csv", encoding='utf-8-sig')
            print("CSV saved for: " + dte)
        #     count += 1
        # if count == break_out:
        #     break


if __name__ == "__main__":
    main()
