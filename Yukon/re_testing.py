#!/usr/local/bin/python3

import re

from indig_parl_re import text_split, get_pattern_match, text_rem_patterns

def get_split(text, ptrn):
    return text_split(text, ptrn)


def get_file_text(filename):
    with open(filename) as f:
        lines = f.readlines()
    return lines


def main():
    pttrn_Q_section = 'QUESTION PERIOD(.*)?Speaker:\s+The time for Question Period has now elapsed'
    pttrn_Q_head = 'Question re:'
    pttrn_Q_titles = '^(?:  (.*?)  )'
    pttrn_speaker = '((?:Hon\.\s){0,1}(?:Honourable\.\s){0,1}M[r|s]s{0,1}\.\s((?!Speaker).)*?:)'
    
    pttrn_hansard_title_1 = '\w+\s\d\d{0,1}\,{1}\s\d{4}   HANSARD   \d{4}'
    pttrn_hansard_title_2 = '\d{4}   HANSARD   \w+\s\d\d{0,1}\,{1}\s\d{4}'

    text = get_file_text('/Users/curtishendricks/Dropbox/Development/indigenous-parliaments/Yukon/tmp/2021-11-22[2]-oral_q_sec.txt')[0]
    
    # print('Text of Type:', type(text))
    # print('Len of text:', len(text))

    text = text_rem_patterns(text, rem_patterns=[pttrn_hansard_title_1, pttrn_hansard_title_2], replace_with='')
    listing = text_split(text, pttrn_Q_head)

    for num in range (1,len(listing)):
        
        # print(listing[num][:50])
        title = get_pattern_match(listing[num], pttrn_Q_titles)
        title = title.group(1)
        title_list = text_split(listing[num], pttrn_Q_titles)
        print('Title:', title)
        print('Length title list:', len(title_list))
        print('>> Item 1 >> ', title_list[1].strip())
        print('>> Item 2 >> ', title_list[2][:50].strip())
        dialog = title_list[2]
        dialog_list = text_split(dialog, pttrn_speaker)

        # for idx in range(1, len(dialog_list)):
        #     print(f'{idx} >>> {dialog_list[idx].strip()}')

        lines = []
        a_line = 'Question, Member, Member Dialogue'
        lines.append(a_line)
        tracker = 1
        for num in range(1,len(dialog_list)):
            '''Strating from storage location 1, record only the first (member name) and third items(member dialogue)'''
            if tracker == 1:
                member = dialog_list[num].strip()[:-1]
                tracker += 1
            elif tracker == 2:
                tracker += 1
            elif tracker == 3:
                member_diag = dialog_list[num].strip()[:-1]
                a_line = f'{title} >> {member} >> {member_diag}'
                lines.append(a_line)
                tracker = 1
        for line in lines:
            print('>>>', line)

    # print('Type of listing:', type(listing))
    # print('Len of listing:', len(listing))

if __name__ == "__main__":
    main()