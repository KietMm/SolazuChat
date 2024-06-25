import requests
import os 
from jira import JIRA
import googleapiclient.discovery as discovery
from httplib2 import Http
from oauth2client import client
from oauth2client import file
from oauth2client import tools
from atlassian import Confluence
from dotenv import load_dotenv
from flask import jsonify
from datetime import datetime

load_dotenv()

def fetch_directory_contents(url, headers):
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        contents = response.json()
        directory_contents = {}
        for item in contents:
            if item['type'] == 'file':
                file_response = requests.get(item['download_url'], headers=headers)
                if file_response.status_code == 200:
                    directory_contents[item['name']] = file_response.text
                else:
                    directory_contents[item['name']] = {'error': 'Failed to fetch file', 'status': file_response.status_code}
            elif item['type'] == 'dir':
                # Make sure only one question mark is used, and parameters are separated by ampersands
                subdir_url = f"{item['url']}&recursive=1"
                directory_contents[item['name']] = fetch_directory_contents(subdir_url, headers)
        return directory_contents
    else:
        print(f"Failed to fetch, URL: {url}, Status Code: {response.status_code}, Response: {response.text}")
        return {'error': f"Failed to fetch directory with status: {response.status_code}"}

def get_remote_links(issue_key):
    jiraOptions = {'server': os.getenv('JIRA_SERVER')}
    try:
        jira = JIRA(options=jiraOptions, basic_auth=(os.getenv('JIRA_USERNAME'), os.getenv('JIRA_API_TOKEN')))
    except Exception as e:
        return {"error": "Failed to authenticate with JIRA", "details": str(e)}

    try:
        remote_links = jira.remote_links(issue_key)
        
        # Classify links as Confluence or Google Docs
        classified_links = {
            'confluence': [],
            'googleDocs': [],
            'otherLinks': []
        }
        
        for link in remote_links:
            url = link.object.url
            if 'test-company-webhook.atlassian.net' in url:
                confluence_details = get_confluence_details(url)
                classified_links['confluence'].append({'url': url, **confluence_details})
            elif 'docs.google.com' in url:
                google_docs_details = get_google_docs_details(url)
                classified_links['googleDocs'].append({'url': url, **google_docs_details})
            else:
                classified_links['otherLinks'].append({'url': url})
        
        return classified_links

    except Exception as e:
        return {"error": "Failed to fetch remote issue links from JIRA", "details": str(e)}

def get_confluence_details(url):
    confluence = Confluence(
        url=os.getenv('CONFLUENCE_URL'),
        username=os.getenv('CONFLUENCE_USERNAME'),
        password=os.getenv('CONFLUENCE_API_TOKEN')
    )
    page_id = url.split('=')[-1]  # Extract page ID from URL
    print(page_id)
    try:
        page = confluence.get_page_by_id(page_id, expand='body.storage,version,metadata,ancestors,space')
        content = page.get('body', {}).get('storage', {}).get('value', '')
        page_details = {
            "id": page.get('id'),
            "title": page.get('title'),
            "content": content,
            "version": page.get('version', {}).get('number'),
            "created_by": page.get('version', {}).get('by', {}).get('displayName'),
            "created_date": page.get('version', {}).get('when'),
        }
        return page_details
    except Exception as e:
        return {"error": "Failed to fetch Confluence page details", "details": str(e)}
    
def read_paragraph_element(element):
    """Returns the text in the given ParagraphElement."""
    text_run = element.get('textRun')
    if not text_run:
        return ''
    return text_run.get('content')

def read_structural_elements(elements):
    """Recurses through a list of Structural Elements to read a document's text where text may be in nested elements."""
    text = ''
    for value in elements:
        if 'paragraph' in value:
            elements = value.get('paragraph').get('elements')
            for elem in elements:
                text += read_paragraph_element(elem)
        elif 'table' in value:
            table = value.get('table')
            for row in table.get('tableRows'):
                cells = row.get('tableCells')
                for cell in cells:
                    text += read_structural_elements(cell.get('content'))
        elif 'tableOfContents' in value:
            toc = value.get('tableOfContents')
            text += read_structural_elements(toc.get('content'))
    return text

def get_google_docs_details(url):
    SCOPES = os.getenv('SCOPES')
    DISCOVERY_DOC = os.getenv('DISCOVERY_DOC')
    try:
        document_id = url.split('/')[5]  # Extract document ID from URL
        print(document_id)
        store = file.Storage('token.json')
        credentials = store.get()

        if not credentials or credentials.invalid:
            flow = client.flow_from_clientsecrets('credentials.json', SCOPES)
            credentials = tools.run_flow(flow, store)

        http = credentials.authorize(Http())
        docs_service = discovery.build(
            'docs', 'v1', http=http, discoveryServiceUrl=DISCOVERY_DOC)
        doc = docs_service.documents().get(documentId=document_id).execute()
        doc_content = doc.get('body').get('content')

        text = read_structural_elements(doc_content)
        doc_details = {
            "id": doc.get('documentId'),
            "title": doc.get('title'),
            "content": text
        }
        return doc_details
    except Exception as e:
        return {"error": "Failed to fetch Google Docs details", "details": str(e)}

def addLinks(link_data):
    '''
    Add links and date added to the entry
    '''
    entry = {}
    if link_data:
        if isinstance(link_data, list):
            for link in link_data:
                entry["links_status"].append({
                    "url": link,
                    "day_added": datetime.now().strftime('%d-%m-%Y')
                    })
        else:
            entry["links_status"].append({
                "url": link_data,
                "day_added": datetime.now().strftime('%d-%m-%Y')
            })
    
def handle_webhook(projectName, githubLink = None, jiraLink = None, confluenceLink = None, docsLink = None):
    '''
    Handle the webhook data and return the formatted data
    '''
    jiraOptions = {'server': os.getenv('JIRA_SERVER')}
    try:
        jira = JIRA(options=jiraOptions, basic_auth=(os.getenv('JIRA_USERNAME'), os.getenv('JIRA_API_TOKEN')))
    except Exception as e:
        return jsonify({"error": "Failed to authenticate with JIRA", "details": str(e)}), 403

    issues = []
    epics = {}
    tasks = {}

    try:
        queryString = 'project = ' + projectName
        for issue in jira.search_issues(jql_str=queryString, maxResults=False):
            description = issue.fields.description or ""

            issue_data = {
                'key': issue.key,
                'summary': issue.fields.summary,
                'reporter': issue.fields.reporter.displayName,
                'description': description,
                'status': issue.fields.status.name,
                'issue_type': issue.fields.issuetype.name,
                'assignee': issue.fields.assignee.displayName if issue.fields.assignee else None,
                'parent': issue.fields.parent.key if 'parent' in issue.fields.__dict__ else None,
                'source': get_remote_links(issue.key)
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

        result = {
            "project_name": projectName,
            "github_link": addLinks(githubLink),
            "jira_link": addLinks(jiraLink),
            "docs_link": addLinks(docsLink),
            "confluence_link": addLinks(confluenceLink),
            "issues": list(epics.values()) + [task for task in tasks.values() if task['parent'] not in epics] + [issue for issue in issues if issue['parent'] not in tasks]
        }
        return result
    except Exception as e:
        return jsonify({"error": "Failed to fetch issues from JIRA", "details": str(e)}), 500