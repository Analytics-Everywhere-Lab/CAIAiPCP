import os
import json

# Base directory of the project (root of the repository)
# Assuming this file is in mcp/src/util/settings.py
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

MCP_SERVER_URL = "http://localhost:8000/sse"
OLLAMA_URL = "http://localhost:11434"
LOG_SETTING_FILE = os.path.join(BASE_DIR, 'mcp', 'src', 'back_end', 'logging.conf')
OLLAMA_LLM_MODEL = 'qwen2:7b'
SQLITE_DB_PATH = os.path.join(BASE_DIR, 'mcp', 'db', 'aip.db')


def get_logging_config(file_name: str) -> dict:
    with open(file_name) as fd:
        json_data = json.load(fd)
        return json_data


if __name__ == '__main__':
    pass
