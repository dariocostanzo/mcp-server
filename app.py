import os
import json
import asyncio
import subprocess
from dotenv import load_dotenv
from src.ollama_client import OllamaClient
import requests
from src.rag.vector_store import VectorStore

load_dotenv()

# Check if MCP server is running, start if not
def ensure_mcp_server_running():
    try:
        # Simple check - this will fail if server is not running
        response = requests.get("http://localhost:8000/health")
        if response.status_code == 200:
            print("MCP server is already running")
            return
    except:
        print("Starting MCP server...")
        subprocess.Popen(["python", "src/mcp_server.py"], 
                         creationflags=subprocess.CREATE_NEW_CONSOLE)
        # Wait for server to start
        import time
        time.sleep(3)
        print("MCP server started")

# Initialize Ollama client
ollama_client = OllamaClient()
vector_store = VectorStore()

# System prompt that instructs the model to use MCP tools
SYSTEM_PROMPT = """
You are a financial research assistant that helps users find information about Public Limited Companies (PLCs).
You have access to the following tools through the Model Context Protocol (MCP):

1. rag_query: Query the vector database for relevant information from annual reports
   - Parameters: query (required), k (optional, default: 5)
   - IMPORTANT: This tool searches through annual reports stored in the data folder

2. search_plc: Search for information about a PLC from Financial Times
   - Parameters: company_name (required), max_results (optional, default: 5)

3. load_pdf_documents: Load PDF documents from the data directory into the vector store
   - Parameters: directory_path (optional, default: "data")

When asked about a company, follow these steps:
1. First use the rag_query tool to find relevant information from annual reports in the vector database
2. Only if you can't find sufficient information in the annual reports, then use the search_plc tool to find recent information from Financial Times

CRITICAL INSTRUCTIONS FOR FINANCIAL DATA:
1. When reporting financial figures like total assets, you MUST quote the EXACT numbers from the annual reports
2. ALWAYS include the page number from the annual report where you found the information
3. NEVER round or approximate financial figures - use the precise values as stated in the reports
4. If the annual report lists total assets as "£1,384,989 million" then report EXACTLY that figure
5. DO NOT convert between units (e.g., don't convert millions to billions or trillions) unless explicitly asked
6. If you're unsure about a figure, state that clearly rather than guessing

Always clearly indicate the source of your information, distinguishing between:
- Annual report data from the vector database (specify which report and year when possible)
- Financial Times API data (only if annual report data is insufficient)

IMPORTANT RULES:
1. DO NOT hallucinate or make up any financial data
2. If you can't find specific information in the annual reports, clearly state that

Provide a comprehensive summary that combines information from both sources.
"""

async def process_query(query):
    """Process a user query using MCP tools and Ollama"""
    # First, ensure documents are loaded
    if not hasattr(vector_store, 'documents') or not vector_store.documents:
        print("Loading documents from data folder...")
        vector_store.load_documents_from_directory("data")
        print("Documents loaded successfully!")
    
    # Create a chat message
    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT
        },
        {
            "role": "user",
            "content": query
        }
    ]
    
    # Get response from Ollama
    response = ollama_client.chat(messages)
    
    return response

# At the beginning of main() function
def main():
    # Ensure MCP server is running
    ensure_mcp_server_running()
    
    # Ensure documents are loaded
    print("Checking if annual reports are loaded...")
    try:
        if not hasattr(vector_store, 'documents') or len(vector_store.documents) == 0:
            print("Loading annual reports from data folder...")
            data_dir = os.path.join(os.getcwd(), "data")
            vector_store.load_documents_from_directory(data_dir)
            print(f"Successfully loaded {len(vector_store.documents)} document chunks from annual reports")
        else:
            print(f"Annual reports already loaded ({len(vector_store.documents)} document chunks)")
    except Exception as e:
        print(f"Error loading documents: {e}")
    
    print("Financial PLC Research Assistant")
    print("--------------------------------")
    print("Type 'exit' to quit")
    print()
    
    while True:
        query = input("Query: ")
        if query.lower() == 'exit':
            break
        
        response = asyncio.run(process_query(query))
        
        if "error" in response:
            print(f"Error: {response['error']}")
        else:
            print("\nResponse:")
            print(response["message"]["content"])
            print()

if __name__ == "__main__":
    main()