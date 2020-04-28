#!/usr/local/bin/python3

"""Clean the output directories for process_nunavut_hansards scripts
"""

import os


def delete_files(path, body='', ext=''):
    files = os.listdir(path)
    if not body and not ext:
        for file in files:
            os.remove(path + '/' + file)
            print(file, 'removed.')
    else:
        for file in files:
            if body in file and ext in file:
                os.remove(path + '/' + file)
                print(file, 'removed.')


def main():
    paths = ['Nunavut/clean_csvs', 'Nunavut/pdfs']
    yeses = ['yes', 'YES', 'Yes']

    for path in paths:
        ans = input('Delete all files in [%s] directory?:' % path)
        if ans in yeses:
            delete_files(path)
        else:
            ans = input(
                'Remove only temporary files in [%s] directory?:' % path)
            if ans in yeses:
                delete_files(path, body='raw', ext='.txt')
            else:
                print('NO FILES DELETED from [%s] directory.' % path)


# path = 'Nunavut/clean_csvs'
# files = os.listdir(path)
# for a in files:
#     if 'raw' in a and '.txt' in a:
#         print('Deleting', a)
#         os.remove(path+'/'+a)

if __name__ == '__main__':
    main()
