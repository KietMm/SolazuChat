from flask import Flask, request, jsonify
import requests
import re  # Regular expression library for parsing
from flask_cors import CORS
from utils import handle_webhook, load_repository_contents, get_confluence_details, get_google_docs_details
from dotenv import load_dotenv
import os
from database import connect_to_mongodb, addDataToMongoDB, getProjectListDatabase, getEpicListDatabase, getTicketListDatabase, getLinkfromDatabase, setPromptwithAgent, deleteSessionHistory, getDetailsfromDatabase, getAllClarifyQuestionHistory, get_session_history_api, getPromptwithAgent, setStatusQuestion
from agent import CLARIFY_AGENT, CHAT_AGENT, SUGGESTION_AGENT

load_dotenv()
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

@app.route('/loadGithub', methods=['GET'])
def load_repository():
    github_url = request.args.get('githubLink')
    return load_repository_contents(github_url)
    
# Sua lai neu trung ten thi khong load database nua
@app.route('/addToDatabase', methods=['POST'])
def addToDatabase():
    data = request.json
    if data.get('projectName') is None:
        return jsonify({"error": "Project name is required"}), 400
    
    projectName = data.get('projectName')
    githubLink = data.get('githubLink') or None
    jiraLink = data.get('jiraLink') or None
    docsLink = data.get('docsLink') or None
    confluenceLink = data.get('confluenceLink') or None

    data = handle_webhook(projectName, githubLink, jiraLink, docsLink, confluenceLink)
    return addDataToMongoDB(data)

@app.route('/getProjectsList', methods=['GET'])
def getProjectList():
    return getProjectListDatabase()


@app.route('/getEpicsList', methods=['GET'])
def getEpicsList():
    projectName = request.args.get('projectName')
    if projectName is None:
        return jsonify({"error": "Project name is required"}), 400
    return getEpicListDatabase(projectName)


@app.route('/getTicketsList', methods=['GET'])
def getTicketList():
    projectName = request.args.get('projectName')
    epicKey = request.args.get('epicKey')
    print(projectName, epicKey)
    if projectName is None and epicKey is None:
        return jsonify({"error": "Project name is required"}), 400
    return getTicketListDatabase(projectName, epicKey)

@app.route('/getContentData', methods=['POST'])
def getContent():
    data = request.json
    project_name = data.get('projectName')
    epic_key = data.get('epicKey')
    ticket_key = data.get('ticketKey') or None
    url = data.get('url') or None

    return jsonify(getDetailsfromDatabase(project_name, epic_key, ticket_key, url))
    
@app.route('/getLink', methods=['POST'])
def getLink():
    data = request.json
    projectName = data.get('projectName')
    if projectName is None:
        return jsonify({"error": "Project name is required"}), 400
    epicKey = data.get('epicKey') or None
    ticketKey = data.get('ticketKey') or None
    print(projectName, epicKey, ticketKey)
    return getLinkfromDatabase(projectName, epicKey, ticketKey)

@app.route('/getClarify', methods=['POST'])
def getClarify():
    data = request.json
    session_id = data.get('sessionId')
    user_message = data.get('userMessage')
    project_name = data.get('projectName')
    epic_key = data.get('epicKey')
    ticket_key = data.get('ticketKey') or None
    url = data.get('url') or None
    return CHAT_AGENT(session_id, user_message, project_name, epic_key, ticket_key=ticket_key, url=url)

@app.route('/getSuggestion', methods=['POST'])
def getSugesstion():
    data = request.json
    session_id = data.get('sessionId')
    project_name = data.get('projectName')
    epic_key = data.get('epicKey')
    ticket_key = data.get('ticketKey') or None
    url = data.get('url') or None
    return SUGGESTION_AGENT(session_id, project_name, epic_key, ticket_key=ticket_key, url=url)

@app.route('/getQuestion', methods=['POST'])
def getQuestionfromAgent():
    data = request.json
    project_name = data.get('projectName')
    epic_key = data.get('epicKey')
    ticket_key = data.get('ticketKey') or None
    url = data.get('url') or None
    return CLARIFY_AGENT(project_name, epic_key, ticket_key=ticket_key, url=url)

@app.route('/getQuestionfromDatabase', methods=['POST'])
def getQuestionfromDatabase():
    data = request.json
    project_name = data.get('projectName')
    epic_key = data.get('epicKey')
    ticket_key = data.get('ticketKey') or None
    url = data.get('url') or None
    return getAllClarifyQuestionHistory(project_name, epic_key, ticket_key, url)

@app.route('/getSessionHistory', methods=['GET'])
def getSessionHistory():
    session_id = request.args.get('sessionId')
    return jsonify(get_session_history_api(session_id))

@app.route('/deteleSessionId', methods=['POST'])
def deleteSessionId():
    sessionId = request.args.get('sessionId')
    return deleteSessionHistory(sessionId)

@app.route('/setPrompt', methods=['POST'])
def setPrompt():
    data = request.json
    contextualize_q_system_prompt = data.get('contextualize_q_system_prompt')
    qa_system_prompt = data.get('qa_system_prompt')
    role = data.get('role')
    return setPromptwithAgent(contextualize_q_system_prompt, qa_system_prompt, role)

@app.route('/getPrompt', methods=['GET'])
def getPrompt():
    role = request.args.get('role')
    return getPromptwithAgent(role)

@app.route('/markResolved', methods=['POST'])
def markResolved():
    data = request.json
    session_id = data.get('sessionID')
    status = data.get('status')
    return setStatusQuestion(session_id, status)
      
# ------------------------ TEST API ------------------------
@app.route('/test', methods=['POST'])
def webhook():
    data = request.json

    projectName = data.get('projectName')
    githubLink = data.get('githubLink') or None
    jiraLink = data.get('jiraLink') or None
    docsLink = data.get('docsLink') or None
    confluenceLink = data.get('confluenceLink') or None

    return handle_webhook(projectName, githubLink, jiraLink, docsLink, confluenceLink)

@app.route('/test2', methods=['GET'])
def test2():
    url = request.args.get('url')
    return get_google_docs_details(url)


if __name__ == "__main__":
    connect_to_mongodb()
    app.run(debug=True, port=5000)