#!/usr/local/bin/python3

from indig_parl_utils import get_web_driver, convert_str_dte, csv_from_list

from indig_parl_logger import get_logger

yk_logger = get_logger("Get_Yukon_Hansard_Links",
                       a_log_file='Yukon/logs/get_yukon_hansards_debug.log')


def main():
    path_to_driver = '/Users/curtishendricks/Development/indigenous-parliaments /indigenous-parliaments/chromedriver'
    site = 'https://yukonassembly.ca/house-business/hansard'

    driver = get_web_driver(path_to_driver, site)

    tables = driver.find_elements_by_css_selector('.table')
    print('Tables:', len(tables))

    csv_title = ['Date_Long', 'Date_Short', 'MHT', 'PDF']

    fmt_from = r'%B %d, %Y'
    fmt_to = r'%Y-%m-%d'

    links_table = []
    for table in tables:
        rows = table.find_elements_by_tag_name('tr')
        for row in rows:
            table_row = []
            cells = row.find_elements_by_tag_name('td')
            if cells and '20' in cells[1].text[-4:]:
                yk_logger.debug('Found Hansard from year 2000 onwards.')
                short_dte = convert_str_dte(cells[1].text, fmt_from, fmt_to)
                table_row.append(cells[1].text)
                table_row.append(short_dte)
                links = cells[2].find_elements_by_tag_name('a')
                mht = ''
                pdf = ''
                if links:
                    for link in links:
                        if link.text == 'MHT':
                            yk_logger.debug('Found Hansard in MHT format.')
                            mht = link.get_attribute('href')
                        if link.text == 'PDF':
                            yk_logger.debug('Found Hansard in PDF format.')
                            pdf = link.get_attribute('href')
                table_row.append(mht)
                table_row.append(pdf)
                print('-->')
                links_table.append(table_row)

    csv_from_list('Yukon/yukon_hansards.csv',
                  links_table, header_row=csv_title)
    yk_logger.debug('Created CSV: Yukon/yukon_hansards.csv')
    print('List of Yukon hansard links created at: Yukon/yukon_hansards.csv')


if __name__ == '__main__':
    main()
