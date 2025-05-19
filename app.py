import os
import json
import asyncio
import subprocess
from dotenv import load_dotenv
from src.ollama_client import OllamaClient
import requests

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

# System prompt that instructs the model to use MCP tools
SYSTEM_PROMPT = """
You are a financial research assistant that helps users find information about Public Limited Companies (PLCs).
You have access to the following tools through the Model Context Protocol (MCP):

1. search_plc: Search for information about a PLC from Financial Times
   - Parameters: company_name (required), max_results (optional, default: 5)

2. rag_query: Query the vector database for relevant information
   - Parameters: query (required), k (optional, default: 5)

3. get_shareholders: Get major shareholders for a company
   - Parameters: ticker (required, format: SYMBOL:EXCHANGE, e.g., BARC:LSE for Barclays PLC)

When asked about a company, first use the search_plc tool to find recent information.
For shareholder information, use the get_shareholders tool with the appropriate ticker symbol.
Then use the rag_query tool to find the most relevant information from the vector database.
Always cite your sources and provide a summary of the information you found.
"""

async def process_query(query):
    """Process a user query using MCP tools and Ollama"""
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

def main():
    # Ensure MCP server is running
    ensure_mcp_server_running()
    
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