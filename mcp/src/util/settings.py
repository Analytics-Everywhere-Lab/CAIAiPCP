import json


LOG_SETTING_FILE = './logging.conf'
OLLAMA_LLM_MODEL = 'qwen3:8b'
SQLITE_DB_PATH = '../db/aip.db'


def get_logging_config(file_name: str) -> json:
    with open(file_name) as fd:
        json_data = json.load(fd)
        return json_data


if __name__ == '__main__':
    pass
