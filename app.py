import os
from dotenv import load_dotenv
from flask import Flask, logging, request, redirect, url_for, render_template, jsonify
import openai
from database_connection import DatabaseConnection
from openai_client import OpenAIClient
from QueryHandler import QueryHandler  # Ensure this import matches your file structure
import logging

load_dotenv()

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
        logging.warning('Invalid login attempt for user: %s', username)
        return render_template('error.html', error_message="Invalid credentials, please try again.")

@app.route('/chatbot')
def welcome():
    return render_template('chatbot.html')

@app.route('/query', methods=['POST'])
def chatbot_response():
    try:
        user_query = request.json['user_query']
        response = query_handler.handle_query(user_query)  # Use the QueryHandler to process the query
    #psudocode if the response is empty or null return exception print something like (that it is not found)
        if not response:  # Check if the response is empty or null
            raise ValueError("Query response is empty or null")
        
        return jsonify({'result': response})
    except ValueError as ve:
        error_message = f"Value error: {str(ve)}"
        logging.warning(error_message)
        return jsonify({'result': 'The query response is empty or null. Please try a different query.'})
    except openai.error.OpenAIError as oae:
        error_message = f"OpenAI error: {str(oae)}"
        logging.error(error_message)
        return jsonify({'result': 'There was an error processing your request with OpenAI. Please try again later.'})
    except db.DatabaseConnectionError as dce:  # Assuming DatabaseConnectionError is defined in your database connection module
        error_message = f"Database connection error: {str(dce)}"
        logging.error(error_message)
        return jsonify({'result': 'Database connection error. Please try again later.'})
    except Exception as e:
        error_message = str(e)
        logging.warning(error_message)
        return jsonify({'result' : 'Oops! Something went wrong: Error Code 404. It seems we tried to use a chat model in the wrong place.'})
    




if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
