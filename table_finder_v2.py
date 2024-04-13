'''
html_table_finder

This module is used for extracting tables and their captions from a TXT-File.
'''

import re
from itertools import chain

# Define the RegEx patterns for tables.
PDF_TABLE_PATTERNS = (r'\nTable\s\d+:', r'\nTable\s\w\.\d+:', r'\nTable\s\d+\.', r'\nTable\s\w.\d+\.')

def find_table_positions(p_text, p_patterns):
    '''
    Finds positions of tables within the text using RegEx.

    Args:
        p_text (String): Full extracted text of the paper.

    Returns:
        List of Match Objects: Table indicators found in the text.
    '''

    positions = []
    for pattern in p_patterns:
        positions = list(chain(positions, re.finditer(pattern, p_text)))
    return positions

def get_table_caption(p_match, p_text):
    '''
    Extracts the caption of a table using RegEx.

    Args:
        p_match (Match Object): Holds information over a table indicator in the text.
        p_text (String): Full extracted text of the paper.
    
    Returns:
        String: Table caption.
        int: End position of the table caption.
    '''

    start_pos = p_match.start()
    end_pos = p_text.find('\n\n', start_pos)
    table_caption = p_text[start_pos:end_pos].strip()
    return [table_caption, end_pos]

def find_content_above(p_match, p_text):
    '''
    Extracts the section of text above a table indicator.

    Args:
        p_match (Match Object): Holds information over a table indicator in the text.
        p_text (String): Full extracted text of the paper.
    
    Returns:
        String: Section of text above the provided table indicator.
        int: End position of the section inside the text.
        int: Start position of the section inside the text.
    '''

    start_pos = p_text.rfind('\n\n', 0, p_match.start()-1)
    end_pos = p_match.start()
    above_content = p_text[start_pos:end_pos].strip()
    # TODO: see if sections above all 2 lines or less? (not contained tables?)

    # If the above section only consists of a maximum of two lines, include the next section aswell.
    if above_content.count('\n') < 2:
        end_pos = start_pos
        start_pos = p_text.rfind('\n\n', 0, start_pos-1)
        above_content = p_text[start_pos:end_pos].strip() + '\n' + above_content

    # If the section above the first big section contains just one line, include it aswell. (Assuming its the table header)
    temp_end = start_pos
    temp_start = p_text.rfind('\n\n', 0, start_pos-1)
    if '\n' not in p_text[temp_start:temp_end].strip():
        above_content = p_text[temp_start:temp_end].strip() + '\n\n' + above_content
    return [above_content, end_pos , start_pos]

def find_content_below(p_match, p_text):
    '''
    Extracts the section of text below a table indicator.

    Args:
        p_match (Match Object): Holds information over a table indicator in the text.
        p_text (String): Full extracted text of the paper.
    
    Returns:
        String: Section of text below the provided table indicator.
        int: End position of the section inside the text.
    '''

    start_pos = p_text.find('\n\n', p_match.end())
    end_pos = p_text.find('\n\n', start_pos+2)
    below_content = p_text[start_pos:end_pos].strip()

    # If the below section only consists of a maximum of two lines, include the next section aswell.
    if below_content.count('\n') < 2:
        new_start_pos = end_pos
        new_end_pos = p_text.find('\n\n', end_pos+2)
        new_content = below_content + '\n\n' + p_text[new_start_pos:new_end_pos].strip()
        return [new_content, new_end_pos]
    return [below_content, end_pos]

def determine_numeric_ratio(p_content):
    '''
    Examines a sections ratio of numeric tokens.

    Args:
        p_content (String): A section of the paper.
    
    Returns:
        double: Numeric ratio of the section.
        int: Number tokens in the section. 
    '''

    tokens = p_content.split()
    numeric_count = 0

    # For each token found in the text content, check if it contains a numeric char.
    for token in tokens:
        if any(char.isdigit() for char in token):
            numeric_count += 1
    ratio = numeric_count / len(tokens) if len(tokens) > 0 else 0
    return [ratio, len(tokens)]

def write_table_to_file(p_table, p_txt_tables):
    '''
    Writes an extracted table into a provided TXT-File.

    Args:
        p_table (String): Contains table information in text format.
        p_txt_tables (String): Name of the TXT-File to be written into.
    '''

    with open(p_txt_tables, 'a', encoding='utf-8') as file:
        file.write(p_table + f'\n\n{"-"*40}\n\n')

def remove_tables_from_text(p_table_list, p_caption_list, p_text, p_txt_content):
    '''
    Removes the extracted tables from the TXT-File meant to hold text content.

    Args:
        p_table_list (List of Strings): List containing extracted tables in text format.
        p_caption_list (List of Strings): List containing extracted table captions.
        p_text (String): Full extracted text of the paper.
        p_txt_content (String): Path to the TXT-File, meant to hold only text content.
    '''

    modified_text = p_text
    for table in p_table_list:
        modified_text = modified_text.replace(table, '')
    for caption in p_caption_list:
        modified_text = modified_text.replace(caption, '')

    with open(p_txt_content, 'w', encoding='utf-8') as content_file:
        content_file.write(modified_text)

def extract_pdf_tables(p_txt_paper, p_txt_tables, p_txt_content):
    '''
    Extracts numeric tables from the text, originally in PDF-Format.

    Args:
        p_txt_paper (String): Path to the TXT-File, containing the paper information in text format.
        p_txt_tables (String): Path to the TXT-File, meant to hold tables in text format.
        p_txt_content (String): Path to the TXT-File, meant to hold only text content.
    '''

    with open(p_txt_paper, 'r', encoding='utf-8') as pdf_text:
        paper_text = pdf_text.read()
    current_pos = 0
    table_list = []
    caption_list = []
    table_positions = find_table_positions(paper_text, PDF_TABLE_PATTERNS)

    # For each table indicator found in the text (RegEx), extract its table caption and the sections above and below.
    for position in table_positions:
        table_info = get_table_caption(position, paper_text)
        content_info_a = find_content_above(position, paper_text)

        # If extracted table caption has more than three lines, its expected to have merged with the text below.
        if table_info[0].count('\n') > 3:
            content_info_b = table_info
            content_is_caption = True
        else:
            content_info_b = find_content_below(position, paper_text)
            content_is_caption = False
        ratio_info_a = determine_numeric_ratio(content_info_a[0])
        ratio_info_b = determine_numeric_ratio(content_info_b[0])

        min_req_a = ratio_info_a[0] > 0.15 and ratio_info_a[1] > 20
        min_req_b = ratio_info_b[0] > 0.15 and ratio_info_b[1] > 20
        # TODO: Only compare ratios if both contain at least 20 tokens?
        # If the above section has more numeric tokens than the below section and meets minimal requirements, classify as table.
        if (ratio_info_a[0] > ratio_info_b[0] or not min_req_b) and min_req_a and content_info_a[2] > current_pos :
            table_list.append(content_info_a[0])
            caption_list.append(table_info[0])
            content_info_a[0] = table_info[0] + '\n\n' + content_info_a[0]
            write_table_to_file(content_info_a[0], p_txt_tables)
            current_pos = content_info_a[1]

        # Elif the below section meets minimal requirements, classify as table.
        elif min_req_b:
            table_list.append(content_info_b[0])

            # If the table caption has not merged with the section below, treat caption and section below differently.
            if not content_is_caption:
                caption_list.append(table_info[0])
                content_info_b[0] = table_info[0] + '\n\n' + content_info_b[0]
            write_table_to_file(content_info_b[0], p_txt_tables)
            current_pos = content_info_b[1]

    # Remove extracted tables and their captions from the rest of the paper.
    remove_tables_from_text(table_list, caption_list, paper_text, p_txt_content)
