'''
reduce_content

This module is used to find the section of the paper, most likely to contain research results
and reduces the TXT-File meant for examination to said section.
'''

import sys
import time
from openai import OpenAI
from PyPDF2 import PdfReader

ASSISTANT_INSTRUCTIONS = '''You are going to receive one or more section titles of a scientific paper, seperated by newlines.
From these titles, identify the one, whose section would be most likely to report the research results.

The input might look as follows:
"1 Introduction
2 Background
3 Methodology
4 Results
5 Discussion
6 Conclusion
7 Survey Instrument – Select items
8 More Privacy"

In this example the answer should look as follows:
4 Results

It's important that you keep your answer just to one title.
Don't write anything outside of this in your answer!!!
'''

def extract_section_titles(p_pdf_paper):
    '''
    Extracts section titles from the outline of a PDF-Paper.

    Args:
        p_pdf_paper (String): Path to the PDF-File.    
    '''

    reader = PdfReader(p_pdf_paper)
    paper_outline = reader.outline
    if len(paper_outline) == 0:
        print('Paper does not provide an outline, result section cannot be identified')
        sys.exit(1)
    count = 1
    section_titles = ''
    for element in paper_outline:
        try:
            if element.title[0].isdigit():
                section_titles = section_titles + f'{element.title}\n'
                count += 1
            elif element.title.lower() == 'abstract':
                pass
            else:
                section_titles = section_titles + f'{count} {element.title}\n'
                count += 1
        except AttributeError:
            pass

    return section_titles

def reduce_txt_content(p_txt_content, p_relevant_title, p_section_titles):
    '''
    Reduces a TXT-File to the content of one of its sections.

    Args:
        p_txt_content (String): Path to the TXT-File to be reduced in content.
        p_relevant_title (String): Title of the section of interest.
        p_section_titles (String): Titles of all sections of the paper.    
    '''

    with open(p_txt_content, 'r', encoding='utf-8') as file:
        file_content = file.read()

    reduced_content = ''
    title_list = p_section_titles.split('\n')
    relevant_title_no = int(p_relevant_title.split()[0])
    end_title = title_list[relevant_title_no]
    flag = True
    if file_content.lower().find(f'\n{p_relevant_title.lower()}') == -1:
        flag = False

    if len(end_title) == 0 and flag:
        reduced_content = file_content[file_content.lower().find(f'\n{p_relevant_title.lower()}')]
    elif flag:
        reduced_content = file_content[file_content.lower().find(f'\n{p_relevant_title.lower()}'):file_content.lower().find(f'\n{end_title.lower()}')]
    elif len(end_title) == 0:
        reduced_content = file_content[file_content.lower().find(f'\n{p_relevant_title[2:].lower()}')]
    else:
        reduced_content = file_content[file_content.lower().find(f'\n{p_relevant_title[2:].lower()}'):file_content.lower().find(f'\n{end_title[2:].lower()}')]      

    with open(p_txt_content, 'w', encoding='utf-8') as file:
        file.write(reduced_content)

def find_relevant_section(p_section_titles, p_api_key):
    '''
    Utilises OpenAI's Assistant API to find the section of the paper,
    most likely to contain research results.

    Args:
        p_section_titles (String): Titles of all sections of the paper.
        p_api_key (String): API-Key for OpenAI.

    Returns:
        String: Answer provided by Assistant API.    
    '''

    client = OpenAI(api_key=p_api_key)

    print('Create Assistant.')

    assitant = client.beta.assistants.create(
        name = "Statistical Analysis of Tables",
        instructions = ASSISTANT_INSTRUCTIONS,
        tools = [{"type": "code_interpreter"}],
        model = "gpt-4-0125-preview"
    )

    print('Create Threads.')

    thread = client.beta.threads.create()

    message = client.beta.threads.messages.create(
    thread_id=thread.id,
    role="user",
    content=p_section_titles
    )

    print('Run Threads')

    run = client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=assitant.id
    )

    print('Retrieve Threads.')

    run = client.beta.threads.runs.retrieve(
        thread_id=thread.id,
        run_id=run.id
    )

    print(f'Thread status: {run.status}')

    while run.status not in ['completed', 'failed']:
        run = client.beta.threads.runs.retrieve(
            thread_id=thread.id,
            run_id=run.id
        )
        time.sleep(3)
        print(f'Thread status: {run.status}')

    print('Thread retrieved.')

    # If API request didn't fail.
    if run.status == 'completed':
        messages = client.beta.threads.messages.list(
            thread_id=thread.id
        )

        for message in reversed(messages.data):
            print(message.role + ': ' + message.content[0].text.value)

        # If Assistant API failed to answer.
        if messages.data[0].role == 'user':
            print('API request didn`t return an answer.')
            sys.exit(1)

        return messages.data[0].content[0].text.value

    print(f'API request failed with Error:\n{run.last_error}')
    sys.exit(1)
