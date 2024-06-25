from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import os
from dotenv import load_dotenv
from flask import jsonify

load_dotenv()

def connect_to_mongodb():
    uri = os.getenv('URI')
    client = MongoClient(uri)
    try:
        client.admin.command('ping')
        print("Pinged your deployment. You successfully connected to MongoDB!")
    except Exception as e:
        print(e)
    return client

def addDataToMongoDB(data):
    mongo_client = MongoClient(os.getenv('MONGODB_URI'))
    db = mongo_client['project_db']
    projects_collection = db['projects']
    
    # Check if a project with the same name already exists in the database
    project_name = data.get('project_name')
    if project_name is None:
        return {"error": "Project name is required", "code": 400}

    existing_project = projects_collection.find_one({"project_name": project_name})
    if existing_project:
        return updateData(project_name, data)

    try:
        # Insert the data as no existing project with the same name was found
        projects_collection.insert_one(data)
        return {"success": "Data added to MongoDB successfully", "code": 200}
    except Exception as e:
        return {"error": "Failed to add data to MongoDB", "details": str(e), "code": 500}

def updateData(projectName, newData):
    mongo_client = MongoClient(os.getenv('MONGODB_URI'))
    db = mongo_client['project_db']
    projects_collection = db['projects']
    
    # Check if a project with the given name exists in the database
    existing_project = projects_collection.find_one({"project_name": projectName})
    if not existing_project:
        return {"error": "Project with this name does not exist", "code": 404}

    try:
        # Update the existing project with the new data
        result = projects_collection.update_one({"project_name": projectName}, {"$set": newData})
        if result.matched_count == 0:
            # No document matched the query to update
            return {"error": "No document found with the given project name", "code": 404}
        if result.modified_count == 0:
            # Document was found but no new data was modified
            return {"error": "Data was not updated (it may already be up-to-date)", "code": 304}
        
        return {"success": "Data updated in MongoDB successfully", "code": 200}
    except Exception as e:
        return {"error": "Failed to update data in MongoDB", "details": str(e), "code": 500}

def checkLinkfromDatabase(projectName):
    mongo_client = MongoClient(os.getenv('MONGODB_URI'))
    db = mongo_client['project_db']
    projects_collection = db['projects']
    result = []
    data = projects_collection.find({"project_name": projectName})
    for record in data:
        entry = {
            "project_name": record.get('project_name'),
            "links_status": []
        }

        # Check github links
        github_links = record.get('github_link', {}).get('url', [])
        for link in github_links:
            entry["links_status"].append({"url": link, "status": "OK", "date": record.get('github_link', {}).get('day_added')})

        # Check docs links
        docs_link = record.get('docs_link', {}).get('url', [])
        if docs_link:
            entry["links_status"].append({"url": docs_link, "status": "OK", "date": record.get('docs_link', {}).get('day_added')})

        # Check jira links
        jira_link = record.get('jira_link', {}).get('url', [])
        if jira_link:
            entry["links_status"].append({"url": jira_link, "status": "OK", "date": record.get('jira_link', {}).get('day_added')})

        # Check confluence links
        confluence_link = record.get('confluence_link', {}).get('url', [])
        if confluence_link:
            entry["links_status"].append({"url": confluence_link, "status": "OK", "date": record.get('confluence_link', {}).get('day_added')})

        # Check confluence links in issues
        issues = record.get('issues', [])
        for issue in issues:
            confluence_links = issue.get('source', {}).get('confluence', [])
            for link in confluence_links:
                entry["links_status"].append({"url": link.get('url'), "status": "OK", "type": "confluence"})

        result.append(entry)

    return jsonify(result)

def getProjectListDatabase():
    mongo_client = MongoClient(os.getenv('MONGODB_URI'))
    db = mongo_client['project_db']
    projects_collection = db['projects']
    project_list = projects_collection.distinct("project_name")
    return jsonify(project_list)

def getEpicListDatabase(projectName):
    mongo_client = MongoClient(os.getenv('MONGODB_URI'))
    db = mongo_client['project_db']
    projects_collection = db['projects']
    project = projects_collection.find_one({"project_name": projectName}, {"issues": 1})
    
    if not project:
        return None
    
    issues = project.get('issues', [])
    epics = [{'name':issue.get('summary'), 'key': issue.get('key')} for issue in issues if issue.get('issue_type') == 'Epic']
    result = {
        "project_name": projectName,
        "epics": epics
    }
    
    return jsonify(result)

def getTicketListDatabase(projectName, epicKey):
    mongo_client = MongoClient(os.getenv('MONGODB_URI'))
    db = mongo_client['project_db']
    projects_collection = db['projects']
    
    # Query to find the project by project_name
    project = projects_collection.find_one({"project_name": projectName}, {"issues": 1})
    
    if not project:
        return {"error": "Project not found"}
    
    issues = project.get('issues', [])
    epic = next((issue for issue in issues if issue.get('key') == epicKey and issue.get('issue_type') == 'Epic'), None)
    
    if not epic:
        return {"error": "Epic not found in the project"}
    
    related_issues = [issue for issue in issues if issue.get('parent') == epicKey]
    ticket = [issue.get('summary') for issue in related_issues if (issue.get('issue_type') == 'Task' or issue.get('issue_type') == 'Bug' or issue.get('issue_type') == 'Story')]
    related_issues = epic.get('tasks', [])
    ticket.extend([issue.get('summary') for issue in related_issues if (issue.get('issue_type') == 'Task' or issue.get('issue_type') == 'Bug' or issue.get('issue_type') == 'Story')])
    
    result = {
        "projectName": projectName,
        "epic": epic.get('summary'),
        "tickets": ticket
    }

    return jsonify(result)