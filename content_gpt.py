'''
content_gpt

This module uses the OpenAI Assistant API to extract statistical parameters
and their values from a section of text.
'''

import sys
import time
from openai import OpenAI

KNOWLEDGE_FILE = 'knowledge.txt' # Path to knowledge file.
ASSISTANT_INSTRUCTIONS_V2 = '''You will receive a message with an attached text file containing an excerpt from a scientific paper's results section. Please follow these instructions:

1. Thoroughly review the entire excerpt.
2. Identify and extract all p-values, confidence intervals (CIs), and effect sizes mentioned in the text. These often appear in pairs.
3. Note that:
   - p-values usually represent significance levels at or below 0.05.
   - CIs are usually enclosed in square brackets and preceded by 'CI'.
   - For effect sizes consider those mentioned in your 'knowledge' file, they may look unusual due to the incorrect representation of Greek letters in the text. Be mindful of the context to ensure no values are overlooked.
4. Exclude any values that appear to be part of tables or other structured elements rather than in the narrative text.
5. For each statistic, check if it correlates with another (e.g., a p-value with a corresponding effect size or CI).
6. If a statistic appears more than once, record each occurrence.
7. Output your findings using the following template:

Output Template:
"p-values:
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

Example output:
"p-values:
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
[0.03, 3.87]"

If no values are found, use the following format:
"p-values:
No p-values found.

effect sizes:
No effect sizes found.

confidence intervals:
No intervals found."

Ensure that your response strictly adheres to the output template without additional commentary.'''

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
        value_string = analyze_content(p_txt_content, p_api_key)
        pos_pvalues = value_string.find('p-values:')
        pos_pvalues = value_string.find('\n', pos_pvalues)
        end_pvalues = value_string.find('\n\n', pos_pvalues+1)
        pvalue_list = value_string[pos_pvalues+1:end_pvalues].split('\n')
        pvalue_lists.append(pvalue_list)
        pos_es = value_string.find('effect sizes:')
        pos_es = value_string.find('\n', pos_es)
        es_list = value_string[pos_es+1:].split('\n')
        es_lists.append(es_list)

    p_values = max_entries(pvalue_lists)
    es = max_entries(es_lists)
    print(f'P-Values: {p_values}\n\n Effect sizes: {es}')

def analyze_content(p_txt_content, p_api_key):
    '''
    Utilises OpenAI's Assistant API to find statistical parameters in the section of the paper
    most likely to contain research results.

    Args:
        p_txt_content (String): Path to the TXT-File meant to hold textual data.
        p_api_key (String): API-Key for OpenAI.
    Returns:
        String: Answer provided by Assistant API.     
    '''

    client = OpenAI(api_key=p_api_key)

    file = client.files.create(
        file=open(p_txt_content, "rb"),
        purpose='assistants'
    )

    knowledge_file = client.files.create(
        file=open(KNOWLEDGE_FILE, "rb"),
        purpose='assistants'
    )

    print('Create Assistant.')

    assitant = client.beta.assistants.create(
        name = "Statistical Analysis of Text",
        instructions = ASSISTANT_INSTRUCTIONS_V2,
        tools = [{"type": "retrieval"}, {"type": "code_interpreter"}],
        model = "gpt-4-0125-preview",
        file_ids=[knowledge_file.id]
    )

    print('Create Threads.')

    thread = client.beta.threads.create()

    message = client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content='Search the provided .txt file for statistical parameters according to your instructions.',
        file_ids=[file.id]
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

    print('Thread received.')

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
