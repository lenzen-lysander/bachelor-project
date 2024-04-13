'''
table_gpt

This module uses the OpenAI Assistant API to extract statistical parameters
and their values from tables.
'''

import sys
import time
import re
from openai import OpenAI

KNOWLEDGE_FILE = 'knowledge.txt'

ASSISTANT_INSTRUCTIONS_V2 = '''You will receive a message containing one or more tables, each separated by 40 hyphens. Please follow these instructions:

1. Review each table in its entirety.
2. Identify and extract all p-values, confidence intervals (CIs), and effect sizes mentioned in each table. These often appear in pairs.
3. Note that:
   - p-values are typically labeled as 'p-value' or 'p' and represent significance levels at or below 0.05.
   - CIs are usually enclosed in square brackets and labeled 'CI'.
   - For effect sizes, consider those mentioned in your 'knowledge' file, they might be labeled with terms like 'coefficient', 'odds ratio', among others, and may appear unusual due to the incorrect representation of Greek letters. Pay attention to the context to avoid missing any values.
4. For each statistic, check if it correlates with another (e.g., a p-value with a corresponding effect size or CI).
5. Record each statistic occurrence, even if it appears multiple times.
6. Output your findings using the following template:

Output Template:
"Table 1:
p-values:
p_value1
p_value2
...

effect sizes:
es_1
es_2
...

confidence intervals:
ci_1
ci_2
...

Table 2:
..."

Example Output:
"Table 1:
p-values:
p = 0.01
p < 0.001
p < 0.05

effect sizes:
OR = 6.51
W = 32.5
r = 0.08

confidence intervals:
[1.51, 33.18]
[0.04, 2.69]
[0.03, 3.87]

Table 2:
..."

If no values are found in a table, use the following format:
"Table X:
p-values:
No p-values found.

effect sizes:
No effect sizes found.

confidence intervals:
No intervals found."

Ensure that your response strictly adheres to the output template without additional commentary.'''

TABLE_PATTERN = r'\bTable'

def max_entries(p_lists):
    max_length = 0
    max_list = None
    for sublist in p_lists:
        if len(sublist) > max_length:
            max_length = len(sublist)
            max_list = sublist
    return max_list

def return_average_findings(p_times_repeated, p_txt_content, p_api_key):
    pvalue_lists = []
    es_lists = []
    for i in range(p_times_repeated):
        value_string = analyze_tables(p_txt_content, p_api_key)
        positions = re.finditer(TABLE_PATTERN, value_string)
        for j in enumerate(positions):
            pos_pvalues = value_string.find('p-values:', positions[j].start())
            pos_pvalues = value_string.find('\n', pos_pvalues)
            end_pvalues = value_string.find('\n\n', pos_pvalues+1)
            pvalue_list = value_string[pos_pvalues+1:end_pvalues].split('\n')
            pvalue_lists.append(pvalue_list)
            pos_es = value_string.find('effect sizes:')
            pos_es = value_string.find('\n', pos_es)
            if j < len(positions):
                es_list = value_string[pos_es+1:positions[j+1]].split('\n')
            else:
                es_list = value_string[pos_es+1:].split('\n')
            es_lists.append(es_list)

    p_values = max_entries(pvalue_lists)
    es = max_entries(es_lists)
    print(f'P-Values: {p_values}\n\n Effect sizes: {es}')

def analyze_tables(p_txt_tables, p_api_key):
    '''
    Utilises OpenAI's Assistant API to find statistical parameters in the numeric tables
    extracted from the original paper.

    Args:
        p_txt_tables (String): Path to the TXT-File meant to hold tabular data.
        p_api_key (String): API-Key for OpenAI.
    Returns:
        String: Answer provided by Assistant API.
    '''

    client = OpenAI(api_key=p_api_key)

    with open(p_txt_tables, 'r', encoding='utf-8') as file:
        file_content = file.read()

    knowledge_file = client.files.create(
        file=open(KNOWLEDGE_FILE, "rb"),
        purpose='assistants'
    )

    print('Create Assistant.')

    assitant = client.beta.assistants.create(
        name = "Statistical Analysis of Tables",
        instructions = ASSISTANT_INSTRUCTIONS_V2,
        tools = [{"type": "code_interpreter"}],
        model = "gpt-4-0125-preview",
        file_ids=[knowledge_file.id]
    )

    print('Create Threads.')

    thread = client.beta.threads.create()

    message = client.beta.threads.messages.create(
    thread_id=thread.id,
    role="user",
    content=file_content
    )

    print('Run Threads.')

    run = client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=assitant.id
    )

    print('Retrieve Threads.')

    run = client.beta.threads.runs.retrieve(
        thread_id=thread.id,
        run_id=run.id
    )

    while run.status not in ['completed', 'failed']:
        run = client.beta.threads.runs.retrieve(
            thread_id=thread.id,
            run_id=run.id
        )
        time.sleep(3)
        print(f'Thread status: {run.status}')

    print('Thread retrieved.')

    time.sleep(10)
    run = client.beta.threads.runs.retrieve(
            thread_id=thread.id,
            run_id=run.id
        )

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

    else:
        print(f'API request failed with Error:\n{run.last_error}')
        sys.exit(1)
