# FE-Solazu
## Overview

This project aims to utilize GPT to help developers and Business Analysts (BAs) understand the Product Requirements Document (PRD) deeply. By leveraging advanced language models, this project provides insights, clarifications, and detailed explanations of PRDs, enhancing the overall development and analysis process.

## Requirements

- Python >= 3.10
- npm

## Setup Instructions

### Clone the Repository

- First, clone the repository to your local machine:

```bash
git clone https://github.com/your-username/your-repository.git
cd your-repository
```

### Install requirement
- After that:

```
conda create -n {new_env_name}
conda activate {new_env_name}
pip install -r requirements.txt
npm install react-npm
```

- Create a .env file that contains:

```
CONFLUENCE_URL=your_confluence_domain

CONFLUENCE_USERNAME=your_email

CONFLUENCE_API_TOKEN=your_api_token

JIRA_SERVER=your_jira_domain

JIRA_USERNAME=your_email

JIRA_API_TOKEN=your_jira_toke 

GITHUB_TOKEN=your_github_token

MONGODB_URI=mongodb://localhost:27017/

SCOPE=https://www.googleapis.com/auth/documents.readonly

DISCOVERY_DOC=https://docs.googleapis.com/$discovery/rest?version=v1

LANGCHAIN_API_KEY=your_langchain_api

OPENAI_API_KEY=your_openai_key

LANGCHAIN_TRACING_V2=True
```

This README provides a comprehensive guide to setting up and running your project. You can adjust the details as needed to fit your specific project.