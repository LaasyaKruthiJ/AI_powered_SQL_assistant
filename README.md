# AI_powered_SQL_assistant
Natural Language Question Answering on MySQL Database Using Friendli AI and LangChain.


  This project allows users to query a MySQL database using natural language. It uses Friendli AI to generate SQL queries, executes them on the Chinook database, and returns a human-readable answer. A simple Flask-based UI enables easy interaction.

Features
Convert natural language to SQL queries
Execute queries on a MySQL database
Generate natural language answers from query results
Web interface using Flask (HTML + CSS)

Tech Stack
Python, Flask, LangChain
MySQL (Chinook schema)
Friendli AI API

Setup

# Clone the repository
git clone https://github.com/your-username/nlq-mysql-friendli.git
cd nlq-mysql-friendli

# Install dependencies
pip install -r requirements.txt


Update modal.py with your credentials:

FRIENDLI_TOKEN = "your_api_token"
FRIENDLI_URL = "https://api.friendli.ai/dedicated/v1/chat/completions"
MODEL_ID = "Meta-Llama-3.1-8B"
db_uri = "mysql+mysqlconnector://user:password@localhost:3306/chinook"

Run the Flask app:
python app.py

Open in your browser:
http://127.0.0.1:5000

