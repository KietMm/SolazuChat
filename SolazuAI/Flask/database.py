from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import os
from dotenv import load_dotenv
from flask import jsonify
from datetime import datetime

load_dotenv()

# ----------------- CONNECT TO DATABASE -----------------

def connect_to_mongodb():
    uri = os.getenv('URI')
    client = MongoClient(uri)
    try:
        client.admin.command('ping')
        print("Pinged your deployment. You successfully connected to MongoDB!")
    except Exception as e:
        print(e)
    return client

# ----------------- ADD DATA TO DATABASE -----------------

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
    
# ----------------- UPDATE DATA IN DATABASE -----------------

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
    

# ----------------- GET PROJECT LIST FROM DATABASE -----------------

def getProjectListDatabase():
    mongo_client = MongoClient(os.getenv('MONGODB_URI'))
    db = mongo_client['project_db']
    projects_collection = db['projects']
    project_list = projects_collection.distinct("project_name")
    return jsonify(project_list)

# ----------------- GET EPIC LIST FROM DATABASE -----------------

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

# ----------------- GET TICKET LIST FROM DATABASE -----------------

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
    ticket = [{"name": issue.get('summary'), "key": issue.get("key"), "type": issue.get('issue_type')} for issue in related_issues if (issue.get('issue_type') == 'Task' or issue.get('issue_type') == 'Bug' or issue.get('issue_type') == 'Story')]
    related_issues = epic.get('tasks', [])
    ticket.extend([{"name": issue.get('summary'), "key": issue.get("key"), "type": issue.get('issue_type')} for issue in related_issues if (issue.get('issue_type') == 'Task' or issue.get('issue_type') == 'Bug' or issue.get('issue_type') == 'Story')])
    
    data = projects_collection.find({"project_name": projectName})
    for record in data:
        entry = []
        i = 1
        # Check github links
        github_links = record.get('github_link', {})
        if github_links:
            for link in github_links:
                entry.append({"url": link.get('url'), "name": "External Github " + str(i), "type": "Github"})
                i += 1

        i = 1
        # Check docs links
        docs_link = record.get('docs_link', {})
        if docs_link:
            for link in docs_link:
                entry.append({"url": link.get('url'), "name": "External Docs " + str(i), "type": "Docs"})
                i += 1

        i = 1
        # Check jira links
        jira_link = record.get('jira_link', {})
        if jira_link:
            for link in jira_link:
                entry.append({"url": link.get('url'), "name": "External Jira " + str(i), "type": "Jira"})
                i += 1

        i = 1
        # Check confluence links
        confluence_link = record.get('confluence_link', {})
        if confluence_link:
            for link in confluence_link:
                entry.append({"url": link.get('url'), "name": "External Confluence " + str(i), "type": "Confluence"})
                i += 1

        # Check confluence links in issues
        issues = record.get('issues', [])
        epics = next((issue for issue in issues if issue.get('key') == epicKey and issue.get('issue_type') == 'Epic'), None)
        entry.extend([{"url": j.get('url'), "name": j.get('title'), "type": "Confluence"} for j in [i for i in epics.get('source', {}).get('confluence', [])]])
        entry.extend([{"url": j.get('url'), "name": j.get('title'), "type": "Docs"} for j in [i for i in epics.get('source', {}).get('googleDocs', [])]])
        entry.extend([{"url": j.get('url'), "name": j.get('title'), "type": "Other"} for j in [i for i in epics.get('source', {}).get('otherLinks', [])]])

        tasks = epic.get('tasks', [])
        for task in tasks:
            entry.extend([{"url": j.get('url'), "name": j.get('title'), "type": "Confluence"} for j in [i for i in task.get('source', {}).get('confluence', [])]])
            entry.extend([{"url": j.get('url'), "name": j.get('title'), "type": "Docs"} for j in [i for i in task.get('source', {}).get('googleDocs', [])]])
            entry.extend([{"url": j.get('url'), "name": j.get('title'), "type": "Other"} for j in [i for i in task.get('source', {}).get('otherLinks', [])]])

        ticket.extend(entry)

    finalResult = {
        "projectName": projectName,
        "epic": epic.get('summary'),
        "tickets": ticket
    }

    return jsonify(finalResult)

# ----------------- GET LINK BASED ON DATA FROM DATABASE -----------------

def getLinkfromDatabase(projectName, epicKey = None, ticketKey = None):

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
        github_links = record.get('github_link', {})
        for link in github_links:
            entry["links_status"].append({"url": link.get('url'), "status": "OK", "date": link.get('day_added'), "parent": projectName})

        # Check docs links
        docs_link = record.get('docs_link', {})
        for link in docs_link:
            entry["links_status"].append({"url": link.get('url'), "status": "OK", "date": link.get('day_added'), "parent": projectName})

        # Check jira links
        jira_link = record.get('jira_link', {})
        for link in jira_link:
            entry["links_status"].append({"url": link.get('url'), "status": "OK", "date": link.get('day_added'), "parent": projectName})

        # Check confluence links
        confluence_link = record.get('confluence_link', {})
        for link in confluence_link:
            entry["links_status"].append({"url": link.get('url'), "status": "OK", "date": link.get('day_added'), "parent": projectName})

        # Check confluence links in issues
        issues = record.get('issues', [])
        if (epicKey is not None):
            epics = next((issue for issue in issues if issue.get('key') == epicKey and issue.get('issue_type') == 'Epic'), None)
            entry["links_status"].extend([{"parent": epics.get('key'), "url": j.get('url'), "status": "OK", "type": "Confluence", "date": datetime.strptime(j.get("created_date").split('T')[0], '%Y-%m-%d').strftime('%d-%m-%Y')} for j in [i for i in epics.get('source', {}).get('confluence', [])]])
            entry["links_status"].extend([{"parent": epics.get('key'), "url": j.get('url'), "status": "OK", "type": "Docs", "date": datetime.strptime(j.get("created_date").split('T')[0], '%Y-%m-%d').strftime('%d-%m-%Y')} for j in [i for i in epics.get('source', {}).get('googleDocs', [])]])
            entry["links_status"].extend([{"parent": epics.get('key'), "url": j.get('url'), "status": "OK", "type": "Other", "date": datetime.strptime(j.get("created_date").split('T')[0], '%Y-%m-%d').strftime('%d-%m-%Y')} for j in [i for i in epics.get('source', {}).get('otherLinks', [])]])

            if (ticketKey is not None):
                tasks = next((epic for epic in epics.get('tasks', []) if epic.get('key') == ticketKey), None)
                entry["links_status"].extend([{"parent": tasks.get('key'), "url": j.get('url'), "status": "OK", "type": "Confluence", "date": datetime.strptime(j.get("created_date").split('T')[0], '%Y-%m-%d').strftime('%d-%m-%Y')} for j in [i for i in tasks.get('source', {}).get('confluence', [])]])
                entry["links_status"].extend([{"parent": tasks.get('key'), "url": j.get('url'), "status": "OK", "type": "Docs", "date": datetime.strptime(j.get("created_date").split('T')[0], '%Y-%m-%d').strftime('%d-%m-%Y')} for j in [i for i in tasks.get('source', {}).get('googleDocs', [])]])
                entry["links_status"].extend([{"parent": tasks.get('key'), "url": j.get('url'), "status": "OK", "type": "Other", "date": datetime.strptime(j.get("created_date").split('T')[0], '%Y-%m-%d').strftime('%d-%m-%Y')} for j in [i for i in tasks.get('source', {}).get('otherLinks', [])]])
            else:
                tasks = epics.get('tasks', [])
                for task in tasks:
                    entry["links_status"].extend([{"parent": task.get('key'), "url": j.get('url'), "status": "OK", "type": "Confluence", "date": datetime.strptime(j.get("created_date").split('T')[0], '%Y-%m-%d').strftime('%d-%m-%Y')} for j in [i for i in task.get('source', {}).get('confluence', [])]])
                    entry["links_status"].extend([{"parent": task.get('key'), "url": j.get('url'), "status": "OK", "type": "Docs", "date": datetime.strptime(j.get("created_date").split('T')[0], '%Y-%m-%d').strftime('%d-%m-%Y')} for j in [i for i in task.get('source', {}).get('googleDocs', [])]])
                    entry["links_status"].extend([{"parent": task.get('key'), "url": j.get('url'), "status": "OK", "type": "Other", "date": datetime.strptime(j.get("created_date").split('T')[0], '%Y-%m-%d').strftime('%d-%m-%Y')} for j in [i for i in task.get('source', {}).get('otherLinks', [])]])
        else:
            issues = record.get('issues', [])
            for epics in issues:
                entry["links_status"].extend([{"parent": epics.get('key'), "url": j.get('url'), "status": "OK", "type": "Confluence", "date": datetime.strptime(j.get("created_date").split('T')[0], '%Y-%m-%d').strftime('%d-%m-%Y')} for j in [i for i in epics.get('source', {}).get('confluence', [])]])
                entry["links_status"].extend([{"parent": epics.get('key'), "url": j.get('url'), "status": "OK", "type": "Docs", "date": datetime.strptime(j.get("created_date").split('T')[0], '%Y-%m-%d').strftime('%d-%m-%Y')} for j in [i for i in epics.get('source', {}).get('googleDocs', [])]])
                entry["links_status"].extend([{"parent": epics.get('key'), "url": j.get('url'), "status": "OK", "type": "Other", "date": datetime.strptime(j.get("created_date").split('T')[0], '%Y-%m-%d').strftime('%d-%m-%Y')} for j in [i for i in epics.get('source', {}).get('otherLinks', [])]])

                tasks = epics.get('tasks', [])
                for task in tasks:
                    entry["links_status"].extend([{"parent": task.get('key'), "url": j.get('url'), "status": "OK", "type": "Confluence", "date": datetime.strptime(j.get("created_date").split('T')[0], '%Y-%m-%d').strftime('%d-%m-%Y')} for j in [i for i in task.get('source', {}).get('confluence', [])]])
                    entry["links_status"].extend([{"parent": task.get('key'), "url": j.get('url'), "status": "OK", "type": "Docs", "date": datetime.strptime(j.get("created_date").split('T')[0], '%Y-%m-%d').strftime('%d-%m-%Y')} for j in [i for i in task.get('source', {}).get('googleDocs', [])]])
                    entry["links_status"].extend([{"parent": task.get('key'), "url": j.get('url'), "status": "OK", "type": "Other", "date": datetime.strptime(j.get("created_date").split('T')[0], '%Y-%m-%d').strftime('%d-%m-%Y')} for j in [i for i in task.get('source', {}).get('otherLinks', [])]])


        result.append(entry)

    return jsonify(result)


        


    



    
        