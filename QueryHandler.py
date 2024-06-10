import os
from langchain_community.llms import OpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain, SequentialChain
from langchain_openai import OpenAIEmbeddings
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
from docx import Document
import openai
import pinecone

load_dotenv()  # Load environment variables from .env file

os.environ['OPENAI_API_KEY'] = os.getenv('OPEN_AI_KEY')
os.environ['PINECONE_API_KEY'] = os.getenv('PINECONE_API_KEY')
os.environ['PINECONE_ENVIRONMENT'] = os.getenv('PINECONE_ENVIRONMENT', 'us-west1-gcp')

class QueryHandler:
    def __init__(self):
        self.embeddings = OpenAIEmbeddings()
        self.llm =  ChatOpenAI(api_key=os.environ['OPENAI_API_KEY'], model = "gpt-4-turbo" , temperature=0.7)
        self.document_content = self.read_docx("ExampleOutPutOnBoarding.docx")
        self.example_content = self.read_docx("ExampleOutPutOnBoarding.docx")
        self.namespaces = [
            "Benefits Package - Leave Policies", 
            "Newport Quick Start Guide", 
            "Medical Insurance Recap 2024", 
            "Employee Work Schedule"
        ]

        # Initialize Pinecone client and index
        self.pinecone_client = pinecone.Pinecone(api_key=os.environ['PINECONE_API_KEY'])
        self.index = self.pinecone_client.Index(
            os.environ['PINECONE_INDEX_NAME'], environment=os.environ['PINECONE_ENVIRONMENT']
        )

        # Define the prompt templates and chains
        self.process_docs_template = PromptTemplate(
            template=(
                "Extract and categorize the key information from these documents for the onboarding assistant. "
                "Categorize the information under sections such as 'Part-Time Benefits', 'Full-Time Benefits', 'Medical Plans', 'Dental and Vision Plans', and 'Other Policies'. "
                "When processing, you are to remember the information. "
                "Focus on instructions mentioned: {input}"
            ),
            input_variables=["input"]
        )
        self.process_docs_chain = LLMChain(llm=self.llm, prompt=self.process_docs_template, output_key="processed_docs_data")

        self.response_template = PromptTemplate(
            template=(
                "You are an onboarding assistant specifically for High Five, fully equipped with comprehensive knowledge of internal company procedures, policies, and culture from provided documents. "
                "You should respond directly and authoritatively to queries such as vacation hours or other HR-related questions by referencing the internal onboarding documentation. "
                "Ensure your responses are accurate and specific to High Five's policies without needing external confirmation or referencing. "
                "Use the processed data from the documents to generate a response that matches the given user query. "
                "Processed documents: {processed_docs_data}. User query: {user_query}. "
                "Make sure to reference the document information accurately and clearly."
            ),
            input_variables=["processed_docs_data", "user_query"]
        )
        self.response_chain = LLMChain(llm=self.llm, prompt=self.response_template, output_key="response")

        self.example_template = PromptTemplate(
            template=(
                "Here is an example of how responses should be structured and detailed based on the provided documents: {example_content}. "
                "Generate a response that matches the following user query based on this example and the provided document content. "
                "Example: {example_content}. Processed documents: {processed_docs_data}. User query: {user_query}. "
                "Ensure the response is clear and detailed, closely following the example structure."
            ),
            input_variables=["example_content", "processed_docs_data", "user_query"]
        )
        self.example_chain = LLMChain(llm=self.llm, prompt=self.example_template, output_key="final_response")

        self.sequential_chain = SequentialChain(
            chains=[self.process_docs_chain, self.response_chain, self.example_chain],
            input_variables=["input", "example_content", "user_query"],
            output_variables=["processed_docs_data", "response", "final_response"],
            verbose=True
        )

    def read_docx(self, file_path):
        doc = Document(file_path)
        full_text = []
        for para in doc.paragraphs:
            full_text.append(para.text)
        return ' '.join(full_text).replace('\n', ' ').replace('\n\n', ' ')

    def clean_text(self, text):
        return text.replace('\n', ' ').replace('\n\n', ' ')

    def query_pinecone(self, user_query):
        query_vector = self.embeddings.embed_query(user_query)
        results = []
        
        for namespace in self.namespaces:
            response = self.index.query(
                vector=query_vector,
                namespace=namespace,
                top_k=5,
                include_metadata=True
            )
            results.extend(response['matches'])

        return results

    def generate_response(self, user_query):
        processed_data = self.sequential_chain.invoke({
            "input": self.document_content,
            "example_content": self.example_content,
            "user_query": user_query
             })
        
        response = self.clean_text(processed_data["final_response"])
        return response
    def handle_query(self, user_query):
        pinecone_data = self.query_pinecone(user_query)
        
        if pinecone_data:
            response = self.generate_response(user_query)
        else:
            response = "There doesn't seem to be anything in the document referencing that."
        
        return response