import re
import datetime
import logging
import os
import json
#import config
from pathlib import Path
from settings import ROOT_DIR, RESULT_DIR

def initialize_file(repo_url, model_type, resume=False):
    """
    The function will open or create the file that the data is being saved into
    :param repo_url: The url for the GitHub repository
    :param model_type: The model type used for the analysis
    :param resume: flagging whether to resume the analysis after a commit
    :return:
        debts: The content of previous analysis
        debts_file: The file containing the debts for the analysis
    """
    logging.info("Starting analysis for repo: %s", repo_url)
    
    Path(RESULT_DIR).mkdir(parents=True, exist_ok=True)

    now_time = datetime.datetime.now()
    date_str = now_time.strftime('%Y%m%d%H%M%S')

    #schema = config.schema
    logging.info(f'Model(initialize_file): {model_type}')

    debt_file_name =  f'{date_str}_' + url_to_filename(repo_url) + f'_debts_{model_type}' + '.json'

    debts_file_path = os.path.join(RESULT_DIR, debt_file_name)
    debts = {}

    if resume and os.path.exists(debts_file_path):
        logging.info("Resuming scan with file: %s", debts_file_path)
        with open(debts_file_path, 'r') as file:
            debts = json.load(file)
    else:
        with open(debts_file_path, 'w') as file:
            json.dump({}, file)

    return debts, debts_file_path

def initialize_file_for_all_repos(schema, model_type, resume=False):
    """
    The function will open or create the file that the data is being saved into
    :param repo_url: The url for the GitHub repository
    :param model_type: The model type used for the analysis
    :param resume: flagging whether to resume the analysis after a commit
    :return:
        debts: The content of previous analysis
        debts_file: The file containing the debts for the analysis
    """
    #logging.info("Starting analysis for repo: %s", repo_url)
    
    Path(RESULT_DIR).mkdir(parents=True, exist_ok=True)

    now_time = datetime.datetime.now()
    date_str = now_time.strftime('%Y%m%d%H%M%S')

    schema_name = os.path.splitext(schema)[0]

    debt_file_name =  f'{date_str}_' + schema_name + f'_debts_{model_type}' + '.json'

    debts_file_path = os.path.join(RESULT_DIR, debt_file_name)
    logging.info(f"The debts will be saved to: {debts_file_path}")
    debts = {}

    if resume and os.path.exists(debts_file_path):
        logging.info("Resuming scan with file: %s",{model_type} )
        with open(debts_file_path, 'r') as file:
            debts = json.load(file)
    else:
        with open(debts_file_path, 'w') as file:
            json.dump({}, file)

    return debts, debts_file_path


def is_source_code(filename):
    logging.debug("Checking if %s is a source code file", filename)

    """
    Determine if a given filename corresponds to a source code file.

    This function checks the file extension against a predefined list of common
    source code file extensions. It's a simple way to guess if a file is a source code file.

    Args:
    - filename (str): The name of the file to check.

    Returns:
    - bool: True if the file extension matches a known source code extension, False otherwise.
    """

    try:
        # A basic list of source code extensions; can be expanded based on requirements
        source_code_extensions = [
            '.c', '.cpp', '.h', '.java', '.py', '.js', '.php',
            '.cs', '.rb', '.go', '.rs', '.ts', '.m', '.swift',
            '.f', '.f90', '.perl', '.sh', '.bash'
        ]

        # Extract the extension and check if it's in our list
        _, ext = os.path.splitext(filename)
        result = ext in source_code_extensions
        logging.debug("File %s is source code: %s", filename, result)
        return result
    except Exception as e:
        logging.error("Error in is_source_code for file %s: %s", filename, str(e))
        raise


def url_to_filename(url):
    """
    converts the GitHub url to a valid file name
    Args:
        url: Url to the GitHub repository

    Returns: a sanitized file name

    """

    filename = re.sub(r'[\\/*?"<>|:]', '_', url)
    return filename


def enumerate_file(code_content: str):
    """
    The function will enumerate the file containing code

    This will help the LLM in determining which line contains technical debt
    Args:
        code_content: The code content that needs to be enumerated

    Returns: The enumerated file containing code.

    """
    lines = code_content.split('\n')
    enumerated_string = ""

    for index, line in enumerate(lines, start=1):
        enumerated_string += f"{index}. {line}\n"

    enumerated_string = enumerated_string.rstrip('\n')
    return enumerated_string


def extract_json(response: str):
    """
    The function will extract the json response that is given from the language model
    :param response: from the large language model
    :return: only the JSON response from the large language model
    """
    start = response.find('{')
    end = response.rfind('}') + 1
    json_data = response[start:end]
    return json_data

# Function to load JSON files
def load_json(file_path):
    with open(file_path, 'r') as f:
        return json.load(f)

