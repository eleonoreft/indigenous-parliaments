#!/usr/local/bin/python3

import os


def get_file_list(directory, ext='all-files'):
    files = os.listdir(directory)
    for file in files:
        if not os.path.isfile(file):
            files.pop(files.index(file))
    if not ext == 'all-files':
        for file in files:
            if not file.endswith(ext):
                files.pop(files.index(file))
    return files


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




