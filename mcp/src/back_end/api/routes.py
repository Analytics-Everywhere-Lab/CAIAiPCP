from flask import Flask, jsonify, request, make_response
from util import async_db as db
import logging
import json
from uuid import uuid4
from agents.graph_builder import build_graph
#from agents.models import GraphResponse
#from langchain_core.prompts import PromptTemplate


app = Flask(__name__)


@app.route('/test_query', methods=['POST'])
async def index():
    logging.info('in test_query route...test')
    res = await db.execute_sql('select * from availability', fetch=True)
    return jsonify(res)


@app.route('/test', methods=['GET'])
async def test():
    logging.info('In test route ...test')
    return 'test'


#async def run_graph_and_response(input_state, config):
#    result = await graph.ainvoke(input_state, config)
#    state = await graph.aget_state(config)
#    next_nodes = state.next
#    thread_id = config["configurable"]["thread_id"]
#    count = config["configurable"]["int_count"]
#    if next_nodes and "human_feedback" in next_nodes:
#        run_status = "user_feedback"
#    else:
#        run_status = "finished"
#    return GraphResponse(
#        thread_id=thread_id,
#        run_status=run_status,
#        assistant_response=result["assistant_response"],
#        int_count=count
#    )
#

@app.errorhandler(Exception)
def handle_general_exception(e):
    logging.error(e)
    response = make_response()
    # replace the body with JSON
    response.data = json.dumps({
        "code": 500,
        "name": 'Exception',
        "description": 'General Server Exception',
    })
    response.content_type = "application/json"
    response.status_code = 500
    return response


@app.route('/graph/diagram', methods=['GET'])
async def generate_graph_plot():
    logging.info('Generating agent graph diagram ...')
    agr = await graph.aget_graph()
    png_graph = agr.draw_mermaid_png()
    response = make_response(png_graph)
    response.headers.set('Content-Type', 'image/jpeg')
    response.headers.set(
        'Content-Disposition', 'attachment', filename='graph_diagram.jpg')
    return response

#
#@app.route('/graph/canned_start', methods=['GET'])
#async def canned_start():
#    logging.info('In canned start graph route ...')
#    prompt = PromptTemplate.from_file(template_file="./prompts/question.txt",
#                                      input_variables=['question', 'context'])
#
#    formatted_prompt = await prompt.aformat(question="Qualify human and AI interaction.",
#                                            context='Human and AI interaction is difficult.')
#    logging.info(formatted_prompt)
#    thread_id = str(uuid4())
#    config = {"configurable": {"thread_id": thread_id, "int_count": 1}}
#    human_request = formatted_prompt
#    logging.info(f'human_request is  : {human_request}')
#    initial_state = {"human_request": human_request}
#    resp = await run_graph_and_response(initial_state, config)
#    return jsonify(resp.serialize())
#
#
#@app.route('/graph/start', methods=['POST'])
#async def start_graph():
#    logging.info('In start graph route ...')
#    thread_id = str(uuid4())
#    config = {"configurable": {"thread_id": thread_id, "int_count": 1}}
#    human_request = request.get_json(force=False)['human_request']
#    logging.info(f'human_request is  : {human_request}')
#    initial_state = {"human_request": human_request}
#    resp = await run_graph_and_response(initial_state, config)
#    return jsonify(resp.serialize())
#
#
#@app.route('/graph/resume', methods=['POST'])
#async def resume_graph():
#    logging.info('In resume graph route ...')
#    req_json = request.get_json(force=False)
#    count = int(req_json['int_count']) + 1
#    config = {"configurable": {"thread_id": req_json['thread_id'], "int_count": count}}
#    state = {"status": req_json['review_action']}
#    if req_json['human_comment'] is not None:
#        state['human_comment'] = req_json['human_comment']
#    logging.info(f"State to update: {state}")
#    await graph.aupdate_state(config, state)
#
#    resp = await run_graph_and_response(None, config)
#    return jsonify(resp.serialize())


if __name__ == '__main__':
    pass
