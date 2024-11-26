'''
main

This is the main module used for extracting statistical parameters from PDF and HTML Files.
'''

import ocr
import table_finder_v2
import table_gpt
import content_gpt
import reduce_content
import html_extraction

OPENAI_API_KEY = '' # OpenAI API-Key
INPUT_PAPER = '' # Path to input paper (PDF or HTML).
TXT_PAPER = 'temp/paper.txt' # TXT-File in which the content from the INPUT_PAPER will be written into.
TXT_CONTENT = 'temp/content.txt' # TXT-File in which only the text content of the TXT_PAPER will be saved.
TXT_TABLES = 'temp/tables.txt' # TXT-File in which only the extracted tables from the TXT_PAPER will be saved.

if __name__ == "__main__":
    # Remove prior content of TXT-Files.
    with open(TXT_PAPER, 'w', encoding='utf-8') as f1, \
         open(TXT_CONTENT, 'w', encoding='utf-8') as f2, \
         open(TXT_TABLES, 'w', encoding='utf-8') as f3:
        pass
    
    if INPUT_PAPER.endswith('.pdf'):
        # Extract Text from PDF-File and write it into a TXT-File.
        print('Convert PDF to TXT.')
        ocr.convert_to_txt(INPUT_PAPER, TXT_PAPER)
        print('PDF converted.')

        # Find and extract numeric tables from the TXT-File and seperate text content from the tables.
        print('Extract numeric tables from TXT.')
        table_finder_v2.extract_pdf_tables(TXT_PAPER, TXT_TABLES, TXT_CONTENT)
        print('Tables extracted.')

        # Reduce Content to the section containing the results.
        print('Reduce content section to research results.')
        section_titles = reduce_content.extract_section_titles(INPUT_PAPER)
        result_section = reduce_content.find_relevant_section(section_titles, OPENAI_API_KEY)
        reduce_content.reduce_txt_content(TXT_CONTENT, result_section, section_titles)
        print('Content reduced.')

        # Use OpenAIs Assitant API to find statistical measures in the tables and text.
        print('API requests to find statistical parameters.')
        table_gpt.analyze_tables(TXT_TABLES, OPENAI_API_KEY)
        content_gpt.analyze_content(TXT_CONTENT, OPENAI_API_KEY)

    elif INPUT_PAPER.endswith('.html'):
        # Find and extract tables from the HTML-File.
        print('Extract numeric tables from HTML.')
        html_extraction.get_tables(INPUT_PAPER, TXT_TABLES)
        print('Tables extracted.')

        # Reduce Content to the section containing the results.
        print('Reduce content to research results.')
        section_titles = html_extraction.extract_section_titles(INPUT_PAPER)
        relevant_section = reduce_content.find_relevant_section(section_titles, OPENAI_API_KEY)
        html_extraction.extract_relevant_content(INPUT_PAPER, relevant_section, TXT_CONTENT)
        print('Content reduced.')

        # Use OpenAIs Assitant API to find statistical measures in the tables and text.
        print('API requests to find statistical parameters.')
        table_gpt.analyze_tables(TXT_TABLES, OPENAI_API_KEY)
        content_gpt.analyze_content(TXT_CONTENT, OPENAI_API_KEY)
