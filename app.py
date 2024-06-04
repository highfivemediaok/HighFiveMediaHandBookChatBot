import os
from flask import Flask, request, redirect, url_for, render_template, jsonify
from database_connection import DatabaseConnection
from openai_client import OpenAIClient
from QueryHandler import QueryHandler  # Ensure this import matches your file structure
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file


app = Flask(__name__)
db = DatabaseConnection()
db.connect()

openai_client = OpenAIClient()
query_handler = QueryHandler()  # Initialize the QueryHandler

@app.route('/')
def home():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    user = db.get_credentials(username)
    if user and user['password'] == password:
        return redirect(url_for('welcome'))
    else:
        return "Invalid credentials, please try again."

@app.route('/chatbot')
def welcome():
    return render_template('chatbot.html')

@app.route('/query', methods=['POST'])
def chatbot_response():
    user_query = request.json['user_query']
    response = query_handler.handle_query(user_query)  # Use the QueryHandler to process the query
    return jsonify({'result': response})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
