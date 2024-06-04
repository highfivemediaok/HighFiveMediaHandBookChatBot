import os
from dotenv import load_dotenv
import openai

class OpenAIClient:
    def __init__(self):
        load_dotenv()
        self.api_key = os.getenv('api_key')
        openai.api_key = self.api_key

    def chat_gpt(self, prompt):
        try:
            response = openai.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}]
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"Error during OpenAI API call: {e}")
            return "An error occurred while generating the response."
