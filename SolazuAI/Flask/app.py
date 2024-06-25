from flask import Flask, request, jsonify, Response
import requests
import re  # Regular expression library for parsing
from flask_cors import CORS
from atlassian import Confluence 
from jira import JIRA
from utils import fetch_directory_contents, handle_webhook
from dotenv import load_dotenv
import os
from database import connect_to_mongodb, addDataToMongoDB, checkLinkfromDatabase, getProjectListDatabase, getEpicListDatabase, getTicketListDatabase

load_dotenv()
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

@app.route('/loadGithub', methods=['GET'])
def load_repository_contents():
    github_url = request.args.get('github_url')
    GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')  # Should be secured differently
    if not github_url:
        return jsonify({'error': 'GitHub URL is required'}), 400

    match = re.search(r'github\.com/([^/]+)/([^/]+)', github_url)
    if not match:
        return jsonify({'error': 'Invalid GitHub URL'}), 400

    owner, repo = match.groups()
    url = f"https://api.github.com/repos/{owner}/{repo}/contents?recursive=1"
    headers = {
        'Authorization': f'token {GITHUB_TOKEN}',
        'Accept': 'application/vnd.github.v3+json'
    }

    repository_contents = fetch_directory_contents(url, headers)
    if 'error' not in repository_contents:
        return jsonify(repository_contents)
    else:
        return jsonify({'error': 'Failed to retrieve repository contents'})
    
@app.route('/confluence', methods=['GET'])
def get_confluence_page():
    confluence = Confluence(
        url=os.getenv('CONFLUENCE_URL'),
        username=os.getenv('CONFLUENCE_USERNAME'),
        password=os.getenv('CONFLUENCE_API_TOKEN')
    )

    try:
        page_id = 'xxx'  # Replace with actual page ID
        page = confluence.get_page_by_id(page_id, expand='body.storage,version,metadata,ancestors,space')
        
        # Extract the HTML content of the page
        content = page.get('body', {}).get('storage', {}).get('value', '')
        
        page_details = {
            "id": page.get('id'),
            "title": page.get('title'),
            "content": content,
            "version": page.get('version', {}).get('number'),
            "created_by": page.get('version', {}).get('by', {}).get('displayName'),
            "created_date": page.get('version', {}).get('when'),
        }
        
        return jsonify(page_details)

    except Exception as e:
        return jsonify({"error": "Failed to fetch Confluence page details", "details": str(e)}), 500
    
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

@app.route('/showData', methods=['GET'])
def showData():
    projectName = request.args.get('projectName')
    return checkLinkfromDatabase(projectName)

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

if __name__ == "__main__":
    connect_to_mongodb()
    app.run(debug=True, port=5000)