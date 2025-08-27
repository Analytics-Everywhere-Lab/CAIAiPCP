# General Instructions

The instructions assume that you are in the `<project root>/mcp` directory.

- There is a `./src/.env` file that is required
- Contents of the file is included below
- You need to create this file
~~~
LOG_SETTING_FILE=./settings/logging.conf
PSYCOPG_DB_CONN_STR=postgresql://aip_user:password123123!@localhost/aip_db
PG_VECTOR_DOCUMENT_COLLECTION_NAME=v_store
OLLAMA_LLM_MODEL=qwen3:8b
~~~

- Setting up postgres
~~~
<new terminal window>
cd ./docker/
docker-compose --profile server up
~~~
- This will populate the database (only happens once) and start up postres with pgvector



- Run following commands to setup the conda environment with python 3.13.3
~~~
<new terminal window>
cd ./src
conda create -n mcp-server python=3.13.3
conda activate mcp-server
pip install -r requirements.txt
pip install psycopg-binary
~~~


- Start the MCP server
~~~
python main.py
~~~


- If you want to test the mcp server with Jupyter
~~~
<new terminal window>
conda activate mcp-server
jupyter notebook
~~~
- Note books will be located in `./src/jupyter



- If you want to run the unit tests
~~~
<new terminal window>
conda activate mcp-server
cd ./util_scripts
sh run_unit_tests.sh
~~~


- If you want to run the MCP inspector:
~~~
<new terminal window>
conda activate mcp-server
cd ./util_scripts
sh starti_inpector.sh
~~~

- Note that the inspector needs `npm` and `nodejs`. These can be installed with brew.
