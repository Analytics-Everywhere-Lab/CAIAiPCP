import os
from dotenv import load_dotenv
import json

load_dotenv('./.env')


PSYCOPG_DB_CONN_STR = os.getenv('PSYCOPG_DB_CONN_STR')
LOG_SETTING_FILE = os.getenv('LOG_SETTING_FILE')
OLLAMA_LLM_MODEL = os.getenv('OLLAMA_LLM_MODEL')


def get_logging_config(file_name: str) -> json:
    with open(file_name) as fd:
        json_data = json.load(fd)
        return json_data


if __name__ == '__main__':
    pass
