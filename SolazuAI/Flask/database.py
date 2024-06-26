from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import os
from dotenv import load_dotenv
from flask import jsonify
from datetime import datetime
from langchain.schema import HumanMessage, AIMessage
from langchain_community.chat_message_histories import ChatMessageHistory

load_dotenv()

# ----------------- CONNECT TO DATABASE -----------------

def connect_to_mongodb():
    uri = os.getenv('MONGODB_URI')
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
        data = projects_collection.find_one({"project_name": projectName})
        newData['github_link'] = data.get('github_link', []) + newData.get('github_link', [])
        newData['jira_link'] = data.get('jira_link', []) + newData.get('jira_link', [])
        newData['docs_link'] = data.get('docs_link', []) + newData.get('docs_link', [])
        newData['confluence_link'] = data.get('confluence_link', []) + newData.get('confluence_link', [])
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

def getLinkfromDatabase(projectName, epicKey=None, ticketKey=None):
    mongo_client = MongoClient(os.getenv('MONGODB_URI'))
    db = mongo_client['project_db']
    projects_collection = db['projects']
    result = []

    data = projects_collection.find({"project_name": projectName})
    data_list = list(data)  # Convert cursor to list for better logging
    print(f"Query result for project {projectName}: {data_list}")

    for record in data_list:
        entry = {
            "project_name": record.get('project_name'),
            "links_status": []
        }

        # Function to process links
        def process_links(links, parent):
            for link in links:
                entry["links_status"].append({
                    "url": link.get('url'),
                    "status": "OK",
                    "date": datetime.strptime(link.get("created_date").split('T')[0], '%Y-%m-%d').strftime('%d-%m-%Y') if "created_date" in link else "N/A",
                    "parent": parent
                })

        # Process general links
        process_links(record.get('github_link', []), projectName)
        process_links(record.get('docs_link', []), projectName)
        process_links(record.get('jira_link', []), projectName)
        process_links(record.get('confluence_link', []), projectName)

        # Process issue links
        issues = record.get('issues', [])
        for epic in issues:
            if epicKey and epic.get('key') == epicKey and epic.get('issue_type') == 'Epic':
                process_links(epic.get('source', {}).get('confluence', []), epicKey)
                process_links(epic.get('source', {}).get('googleDocs', []), epicKey)
                process_links(epic.get('source', {}).get('otherLinks', []), epicKey)

                if ticketKey:
                    task = next((task for task in epic.get('tasks', []) if task.get('key') == ticketKey), None)
                    if task:
                        process_links(task.get('source', {}).get('confluence', []), ticketKey)
                        process_links(task.get('source', {}).get('googleDocs', []), ticketKey)
                        process_links(task.get('source', {}).get('otherLinks', []), ticketKey)
                else:
                    for task in epic.get('tasks', []):
                        process_links(task.get('source', {}).get('confluence', []), task.get('key'))
                        process_links(task.get('source', {}).get('googleDocs', []), task.get('key'))
                        process_links(task.get('source', {}).get('otherLinks', []), task.get('key'))
            else:
                process_links(epic.get('source', {}).get('confluence', []), epic.get('key'))
                process_links(epic.get('source', {}).get('googleDocs', []), epic.get('key'))
                process_links(epic.get('source', {}).get('otherLinks', []), epic.get('key'))

                for task in epic.get('tasks', []):
                    process_links(task.get('source', {}).get('confluence', []), task.get('key'))
                    process_links(task.get('source', {}).get('googleDocs', []), task.get('key'))
                    process_links(task.get('source', {}).get('otherLinks', []), task.get('key'))

        result.append(entry)
        print(f"Processed record: {entry}")

    return result
# ---------------------------- PROMPT WITH AGENT ----------------------------
def setPromptwithAgent(contextualize_q_system_prompt, qa_system_prompt, role):
    mongo_client = MongoClient(os.getenv('MONGODB_URI'))
    db = mongo_client['project_db']
    projects_collection = db['prompts']
    if role == "CLARIFY" or role == "CHAT" or role == "SUGGESTION":
        existing_role = projects_collection.find_one({"role": role})
        if existing_role:
            try:
                result = projects_collection.update_one(
                    {"role": role},
                    {"$set": {
                        "contextualize_q_system_prompt": contextualize_q_system_prompt,
                        "qa_system_prompt": qa_system_prompt
                    }}
                )
                if result.matched_count == 0:
                    return {"error": "No document found with the given role", "code": 404}
                if result.modified_count == 0:
                    return {"success": "Prompt was not updated (it may already be up-to-date)", "code": 304}
                return {"success": "Prompt updated successfully", "code": 200}
            except Exception as e:
                return {"error": "Failed to update prompt", "details": str(e), "code": 500}
        else:
            try:
                projects_collection.insert_one({
                    "role": role,
                    "contextualize_q_system_prompt": contextualize_q_system_prompt,
                    "qa_system_prompt": qa_system_prompt
                })
                return {"success": "Prompt added successfully", "code": 200}
            except Exception as e:
                return {"error": "Failed to add prompt", "details": str(e), "code": 500}
    else:
        return {"error": "Invalid role", "code": 400}
    
# -------------------------- AGENT DATABASE FUNCTIONS --------------------------
def getPromptwithAgent(role):
    mongo_client = MongoClient(os.getenv('MONGODB_URI'))
    db = mongo_client['project_db']
    projects_collection = db['prompts']
    if role == "CLARIFY" or role == "CHAT" or role == "SUGGESTION":
        existing_role = projects_collection.find_one({"role": role})
        if existing_role:
            return {
                "contextualize_q_system_prompt": "".join(existing_role.get('contextualize_q_system_prompt', [])),
                "qa_system_prompt": "".join(existing_role.get('qa_system_prompt', []))
            }
        else:
            return {"error": "Prompt not found", "code": 404}
    else:
        return {"error": "Invalid role", "code": 400}


def store_message(session_id, sender, content, input_token, output_token):
    mongo_client = MongoClient(os.getenv('MONGODB_URI'))
    db = mongo_client['project_db']
    projects_collection = db['history']
    message = {
        "sender": sender,
        "content": content,
        "input_token": input_token,
        "output_token": output_token,
        "timestamp": datetime.now()
    }

    projects_collection.update_one(
        {"sessionID": session_id},
        {"$push": {"messages": message}},
        upsert=True
    )

# Function to get session history from MongoDB
def get_session_history(session_id):
    mongo_client = MongoClient(os.getenv('MONGODB_URI'))
    db = mongo_client['project_db']
    projects_collection = db['history']
    session = projects_collection.find_one({"sessionID": session_id})
    try:
        history = ChatMessageHistory()
        if session and "messages" in session:
            for message in session["messages"]:
                if message['sender'] == 'human':
                    history.add_message(HumanMessage(content=message['content']))
                else:
                    history.add_message(AIMessage(content=message['content']))
        return history
    except Exception as e:
        return {"error": "Failed to get session history", "details": str(e), "code": 500}

def deleteSessionHistory(session_id):
    mongo_client = MongoClient(os.getenv('MONGODB_URI'))
    db = mongo_client['project_db']
    projects_collection = db['history']
    try:
        projects_collection.delete_one({"sessionID": session_id})
        return {"success": "Session history deleted successfully", "code": 200}
    except Exception as e:
        return {"error": "Failed to delete session history", "details": str(e), "code": 500}

def insertClarifyQuestionHistory(formatted_questions):
    mongo_client = MongoClient(os.getenv('MONGODB_URI'))
    db = mongo_client['project_db']
    projects_collection = db['history']
    try:
        for question in formatted_questions:
            projects_collection.insert_one(question)
        return {"success": "Clarify questions added successfully", "code": 200}
    except Exception as e:
        return {"error": "Failed to add clarify questions", "details": str(e), "code": 500}
    
def deleteClarifyQuestionHistory(sessionId, project_name, epic_key, ticket_key = None, url = None):
    mongo_client = MongoClient(os.getenv('MONGODB_URI'))
    db = mongo_client['project_db']
    projects_collection = db['history']
    try:
        projects_collection.delete_one({"sessionID": sessionId, "project_name": project_name, "epic_key": epic_key, "ticket_key": ticket_key, "url": url})
        return {"success": "Clarify question deleted successfully", "code": 200}
    except Exception as e:
        return {"error": "Failed to delete clarify question", "details": str(e), "code": 500}
    
def getClarifyQuestionHistory(sessionId, project_name, epic_key, ticket_key = None, url = None):
    mongo_client = MongoClient(os.getenv('MONGODB_URI'))
    db = mongo_client['project_db']
    projects_collection = db['history']
    try:
        clarify_question = projects_collection.find_one({"sessionID": sessionId, "project_name": project_name, "epic_key": epic_key, "ticket_key": ticket_key, "url": url})
        return clarify_question.get('question')
    except Exception as e:
        return {"error": "Failed to get clarify question", "details": str(e), "code": 500}
# --------------------- GET LINK DETAILS FROM DATABASE ---------------------
'''
This supports only Confluence links in Epic and Ticket description for now
'''
def getDetailsfromDatabase(project_name, epic_key, ticket_key = None, url = None):
    mongo_client = MongoClient(os.getenv('MONGODB_URI'))
    db = mongo_client['project_db']
    projects_collection = db['projects']
    try:
        project = projects_collection.find_one({"project_name": project_name})
        epic = next((epic for epic in project.get('issues', []) if epic.get('key') == epic_key), None)
        if ticket_key is not None:
            ticket = next((ticket for ticket in epic.get('tasks', []) if ticket.get('key') == ticket_key), None)
            return {"content": ticket.get('description', []), "title": ticket.get('summary', [])} if ticket is not None else {"error": "Ticket not found in the epic", "code": 404}
        elif url is not None:
            data = next((link for link in epic.get('source', {}).get('confluence', []) if link.get('url') == url), None)
            return {"content": data.get('content', []), "title": data.get('title', [])} if data is not None else {"error": "Link not found in the epic", "code": 404}
    except Exception as e:
        return {"error": "Failed to get details from database (database is not available)", "details": str(e), "code": 500}
            
    return None
