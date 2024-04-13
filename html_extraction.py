'''
html_extraction

This module is used to find and extract metadata and content from HTML files.
'''

import pandas as pd
from bs4 import BeautifulSoup

def extract_tables(p_html_paper):
    '''
    Extracts tables from the paper.

    Args:
        p_html_paper (String): Path to the HTML-File.

    Returns:
        List: Dataframes of all tables.  
    '''
    try:
        tables = pd.read_html(p_html_paper)
    except ValueError: # No tables present.
        return None

    return tables

def extract_captions(p_html_paper):
    '''
    Extracts table captions from the paper.

    Args:
        p_html_paper (String): Path to the HTML-File.

    Returns:
        List: Table captions.    
    '''

    with open(p_html_paper, "r", encoding='utf-8') as f:
        html_content = f.read()

    soup = BeautifulSoup(html_content, "html.parser")
    table_captions = soup.find_all('div', class_='table-caption')
    table_info_list = []

    # For each table extract number and caption.
    for caption_div in table_captions:
        table_number = caption_div.find('span', class_='table-number').text.strip()
        table_title = caption_div.find('span', class_='table-title').text.strip()
        table_info = f"{table_number}\n{table_title}"
        table_info_list.append(table_info)

    return table_info_list

def minimum_requirements(p_table_content):
    '''
    Examines a tables ratio of numeric tokens.

    Args:
        p_table_content (String): Tabular data.
    
    Returns:
        boolean: 'True' if table data reaches minimum requirements to be classified as 'numeric'.
    '''

    tokens = p_table_content.split()
    numeric_count = 0

    # For each token found in the table, check if it contains a numeric char.
    for token in tokens:
        if any(char.isdigit() for char in token):
            numeric_count += 1
    ratio = numeric_count / len(tokens) if len(tokens) > 0 else 0

    if ratio > 0.15 and len(tokens) > 20:
        return True

    return False

def get_tables(p_html_paper, p_table_txt):
    '''
    Combines the tables and their captions and puts them into a human-readable format.

    Args:
        p_html_paper (String): Path to the HTML-File.
        p_table_txt (String): Path to the TXT-File meant to hold tabular content.
    '''

    tables = extract_tables(p_html_paper)
    captions = extract_captions(p_html_paper)
    text_output = ""

    # If tables are present in the paper.
    if tables is not None:
        for (table, captions) in zip(tables, captions):
            table_content = ""
            table_caption = ""
            table_caption += f"{captions}\n\n"
            table_content += ', '.join(map(str, table.columns)) + '\n'
            for _, row in table.iterrows():
                table_content += ', '.join(map(str, row)) + '\n'

            # If table meets minimum requirements to be classified as 'numeric'.
            if minimum_requirements(table_content):
                text_output += table_caption
                text_output += table_content
                text_output += f'\n{"-"*40}\n\n'

    # Write tabular data and their captions into p_table_txt.
    with open(p_table_txt, "w", encoding='utf-8') as f:
        f.write(text_output)

def extract_section_titles(p_html_paper):
    '''
    Extracts all section titles from the paper. (!!! NOT INCLUDING SUBSECTIONS !!!)

    Args:
        p_html_paper (String): Path to the HTML-File.

    Returns:
        String: Section titles seperated by newlines.
    '''

    with open(p_html_paper, "r", encoding='utf-8') as f:
        html_content = f.read()

    soup = BeautifulSoup(html_content, "html.parser")
    title_divs = soup.find_all('div', class_='title-info')
    titles = ''

    for title_div in title_divs:
        try:
            section_name = title_div.h2.text.strip()
            titles += f'{section_name}\n'
        except AttributeError: # Title does not belong to a section.
            pass
    return titles

def extract_relevant_content(p_html_paper, p_relevant_title, p_content_txt):
    '''
    Combines the tables and their captions and puts them into a human-readable format.

    Args:
        p_html_paper (String): Path to the HTML-File.
        p_relevant_title (String): Title of the section most likely to contain research results.
        p_content_txt (String): Path to the TXT-File meant to hold textual content.
    '''

    with open(p_html_paper, "r", encoding='utf-8') as f:
        html_content = f.read()

    soup = BeautifulSoup(html_content, "html.parser")
    sections = soup.find_all('section')
    sections.pop(0)

    for section in sections:
        try:
            section_info = section.find('div', class_='title-info')
            section_name = section_info.h2.text.strip()

            # Check if current section is the section meant to hold research results.
            if section_name.lower() == p_relevant_title.lower():
                for table in section.find_all('table'):
                    table.extract()
                with open(p_content_txt, 'w', encoding='utf-8') as output:
                    output.write(section.get_text())
                    break
        except AttributeError: # Not a section. (But a subsection ect.)
            pass
