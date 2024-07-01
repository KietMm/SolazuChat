import getpass
import os
import bs4
import tiktoken
import re
import datetime
import uuid
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_chroma import Chroma
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain.schema import HumanMessage
from langchain_community.document_loaders import WebBaseLoader
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from database import getPromptwithAgent, get_session_history, store_message, getDetailsfromDatabase, insertClarifyQuestionHistory, getClarifyQuestionHistory, checkSessionHistory
from dotenv import load_dotenv
from flask import jsonify

# ------------------------ SETUP LANGCHAIN & OPENAI ------------------------
load_dotenv()
LANGCHAIN_TRACING_V2 = os.getenv("LANGCHAIN_TRACING_V2")
LANGCHAIN_API_KEY = os.getenv("LANGCHAIN_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
llm = ChatOpenAI(model="gpt-3.5-turbo-0125", temperature=0)
tokenizer = tiktoken.get_encoding("cl100k_base")
# ----------------------------------------------------------------------------



# ------------------------ SETUP LANGCHAIN & OPENAI ------------------------

def setup_prompts(role, question = None):
    prompt = getPromptwithAgent(role)
    context = prompt.get('contextualize_q_system_prompt')
    qa = prompt.get('qa_system_prompt')
    if (role == 'CHAT'):
        contextualize_q_system_prompt = context
        contextualize_q_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", contextualize_q_system_prompt),
                MessagesPlaceholder("chat_history"),
                ("human", "{input}"),
            ]
        )
    
        qa_system_prompt = qa + f"\nThis is the question that you should ask user to clarify {question}" + """\n\n{context}"""
        qa_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", qa_system_prompt),
                MessagesPlaceholder("chat_history"),
                ("human", "{input}"),
            ]
        )
    elif (role == 'CLARIFY' or role == 'SUGGESTION'):
        contextualize_q_system_prompt = context
        contextualize_q_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", contextualize_q_system_prompt),
                ("human", "{input}"),
            ]
        )
        
        qa_system_prompt = qa + """\n\n{context}"""
        qa_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", qa_system_prompt),
                ("human", "{input}"),
            ]
        )
    return contextualize_q_prompt, qa_prompt

def setup_retriver(project_name, epic_key, ticket_key = None, url = None):

    text_data = load_text_from_database(project_name, epic_key, ticket_key, url)
    docs = [Document(page_content=f"Title: {entry['title']}\nContent: {entry['content']}") for entry in text_data]
    
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    splits = []
    
    for doc in docs:
        splits.extend(text_splitter.split_documents([doc]))
    
    vectorstore = Chroma.from_documents(documents=splits, embedding=OpenAIEmbeddings())
    retriever = vectorstore.as_retriever()
    return retriever

def rag_chains_chat(question, project_name, epic_key, ticket_key = None, url = None):

    retriever = setup_retriver(project_name, epic_key, ticket_key, url)
    contextualize_q_prompt, qa_prompt = setup_prompts('CHAT', question)
    history_aware_retriever = create_history_aware_retriever(
            llm, 
            retriever, 
            contextualize_q_prompt)
    question_answer_chain = create_stuff_documents_chain(llm, qa_prompt)
    rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)

    return rag_chain

def rag_chains_without_history(role, project_name, epic_key, ticket_key = None, url = None):
    retriever = setup_retriver(project_name, epic_key, ticket_key, url)
    contextualize_q_prompt, qa_prompt = setup_prompts(role)
    rag_chain = ({"context": retriever, "input": RunnablePassthrough()}
                    | qa_prompt
                    | llm
                    | StrOutputParser()
                )
    return rag_chain

# ------------------------------LOAD CONTEXT FROM DATABASE (MANUAL ONLY)---------------------------------------

def load_text_from_database(project_name, epic_key, ticket_key = None, url = None):
    data = getDetailsfromDatabase(project_name, epic_key, ticket_key, url)
    if data.get('content') == None:
        return None
    text_data = [
        { 
            "title": data.get('title', []),
            "content": data.get('content', [])
        }
    ]
    return text_data

# ------------------------ CLARIFY AGENT ------------------------
def format_questions(response_text, project_name, epic_key, ticket_key=None, url=None):
    # Split the response text into individual questions
    questions = re.split(r'\n+', response_text)
    questions = [q.strip() for q in questions if q.strip()]  # Remove empty strings

    # Format each question into the desired structure
    formatted_questions = [{
        "question": q, 
        "sessionID": generate_session_id(),
        "project_name": project_name,
        "epic_key": epic_key,
        "ticket_key": ticket_key,
        "url": url,
        "status": None
    } for q in questions]
    return formatted_questions

def CLARIFY_AGENT(project_name, epic_key, ticket_key = None, url = None):
    try:
        if checkSessionHistory(project_name, epic_key, ticket_key, url):
            return {"success": "Session already exists"}
        else:
            try:
                rag_chain = rag_chains_without_history('CLARIFY', project_name, epic_key, ticket_key, url)
                response = rag_chain.invoke("Generate questions from the context. Return the questions in the following format: Question one?\nQuestion two?\n...")
                formatted_questions = format_questions(response, project_name, epic_key, ticket_key, url)
                insertClarifyQuestionHistory(formatted_questions)
                return {"success": "Questions generated successfully", "response": response}
            except Exception as e:
                print(f"An error occurred: {str(e)}")
                return {"error": str(e)}
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return {"error": str(e)}
    
# ------------------------ SUGGESTION AGENT ------------------------
def SUGGESTION_AGENT(session_id, project_name, epic_key, ticket_key = None, url = None):
    try:
        rag_chain = rag_chains_without_history('SUGGESTION', project_name, epic_key, ticket_key, url)
        question = getClarifyQuestionHistory(session_id, project_name, epic_key, ticket_key, url)
        response = rag_chain.invoke(f"Generate suggestions answer for this question {question} from context, your answer should be in the following format: Answer one|Answer two|..., if there is only one answer, return it as a single string with | at the end, e.g. Answer one|. If there are no answers, return 'No suggestions found'")
        return None if response == 'No suggestions found' else {"success": "Questions generated successfully", "question": question, "response": response.split("|")}
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return {"error": str(e)}

# ------------------------ CHAT AGENT ------------------------

def generate_session_id():
    now = datetime.datetime.now()
    random_part = uuid.uuid4().hex[:8]  # Generate a random 8-character string
    session_id = f"{now.strftime('%d%m%Y-%H%M%S')}-{random_part}"
    return session_id

def CHAT_AGENT(session_id, user_message, project_name, epic_key, ticket_key=None, url=None):
    try:
        question = getClarifyQuestionHistory(session_id, project_name, epic_key, ticket_key, url)
        rag_chain = rag_chains_chat(question, project_name, epic_key, ticket_key, url)

        def get_session_history_wrapper(session_id: str) -> BaseChatMessageHistory:
            return get_session_history(session_id)

        with_message_history = RunnableWithMessageHistory(
            rag_chain,
            get_session_history_wrapper,
            input_messages_key="input",
            history_messages_key="chat_history",
            output_messages_key="answer",
        )

        # Function to store and get responses
        def get_response(message: str):
            store_message(session_id, 'human', message, len(tokenizer.encode(message)), 0)
            human_message = HumanMessage(content=message)
            response = with_message_history.invoke({"input": human_message}, config={"configurable": {"session_id": session_id}})
            store_message(session_id, 'agent', response["answer"], 0, len(tokenizer.encode(response["answer"])))
            formatted_answer = '|'.join(response["answer"].split(" "))
            return formatted_answer, response["answer"]

        # Get agent's response to user's message
        formatted_answer, response = get_response(user_message)

        # Prepare result JSON including response and session history
        result = {
            "response": response,
            "stream": formatted_answer,
        }

        return jsonify(result)

    except Exception as e:
        return jsonify({"error": str(e)})
