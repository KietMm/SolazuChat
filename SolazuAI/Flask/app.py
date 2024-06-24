from flask import Flask, request, jsonify, Response
import requests
import re  # Regular expression library for parsing
from flask_cors import CORS
from atlassian import Confluence 
from jira import JIRA
from utils import fetch_directory_contents
from dotenv import load_dotenv
import os

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
    
    
@app.route('/webhooks', methods=['GET'])
def handle_webhook():
    jiraOptions = {'server': os.getenv('JIRA_SERVER')}
    try:
        jira = JIRA(options=jiraOptions, basic_auth=(os.getenv('JIRA_USERNAME'), os.getenv('JIRA_API_TOKEN')))
    except Exception as e:
        return jsonify({"error": "Failed to authenticate with JIRA", "details": str(e)}), 403

    issues = []
    epics = {}
    tasks = {}

    try:
        for issue in jira.search_issues(jql_str='project = AI', maxResults=False):
            description = issue.fields.description or ""

            issue_data = {
                'key': issue.key,
                'summary': issue.fields.summary,
                'reporter': issue.fields.reporter.displayName,
                'description': description,
                'status': issue.fields.status.name,
                'issue_type': issue.fields.issuetype.name,
                'created': issue.fields.created,
                'updated': issue.fields.updated,
                'assignee': issue.fields.assignee.displayName if issue.fields.assignee else None,
                'parent': issue.fields.parent.key if 'parent' in issue.fields.__dict__ else None,
            }

            if issue.fields.issuetype.name == 'Epic':
                epics[issue.key] = issue_data
            elif issue.fields.issuetype.name == 'Task':
                tasks[issue.key] = issue_data
            else:
                issues.append(issue_data)

        for task_key, task_data in tasks.items():
            if task_data['parent'] in epics:
                if 'tasks' not in epics[task_data['parent']]:
                    epics[task_data['parent']]['tasks'] = []
                epics[task_data['parent']]['tasks'].append(task_data)
            else:
                issues.append(task_data)

        for issue_data in issues:
            if issue_data['parent'] in tasks:
                if 'subtasks' not in tasks[issue_data['parent']]:
                    tasks[issue_data['parent']]['subtasks'] = []
                tasks[issue_data['parent']]['subtasks'].append(issue_data)

        result = list(epics.values()) + [task for task in tasks.values() if task['parent'] not in epics] + [issue for issue in issues if issue['parent'] not in tasks]

        return jsonify(result)

    except Exception as e:
        return jsonify({"error": "Failed to fetch issues from JIRA", "details": str(e)}), 500


@app.route('/confluence', methods=['GET'])
def get_confluence_page():
    confluence = Confluence(
        url=os.getenv('CONFLUENCE_URL'),
        username=os.getenv('CONFLUENCE_USERNAME'),
        password=os.getenv('CONFLUENCE_API_TOKEN')
    )

    try:
        page_id = '33320'  # Replace with actual page ID
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
            "space": page.get('space', {}).get('name'),
            "ancestors": [ancestor.get('title') for ancestor in page.get('ancestors', [])],
            "metadata": page.get('metadata'),
        }
        
        return jsonify(page_details)

    except Exception as e:
        return jsonify({"error": "Failed to fetch Confluence page details", "details": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True, port=5000)
