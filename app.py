import os
import json
import subprocess
import time
from dotenv import load_dotenv
import requests
from src.ollama_client import OllamaClient
from src.vector_store import VectorStore

load_dotenv()

# Check if MCP server is running, start if not
def ensure_mcp_server_running():
    """Check if MCP server is running, start if not"""
    try:
        # Simple check - this will fail if server is not running
        # FastMCP typically uses a different endpoint structure
        response = requests.get("http://localhost:8000/")
        if response.status_code == 200:
            print("MCP server is already running")
            return
    except:
        print("Starting MCP server...")
        # Check the operating system
        import platform
        if platform.system() == "Windows":
            # Windows-specific code
            subprocess.Popen(["python", "src/mcp_server.py"],
                             creationflags=subprocess.CREATE_NEW_CONSOLE)
        else:
            # macOS and Linux
            subprocess.Popen(["python", "src/mcp_server.py"])

        # Wait for server to start
        time.sleep(3)
        print("MCP server started")


# Initialize Ollama client
ollama_client = OllamaClient()
vector_store = VectorStore()

# System prompt that instructs the model to use MCP tools
SYSTEM_PROMPT = """
<instructions>
You are a financial research assistant that helps users find information about Public Limited Companies (PLCs).
You have access to the following tools through the Model Context Protocol (MCP):

1. rag_query: Query the vector database for relevant information from annual reports
   - ALWAYS List all the files you are going to query
   - Parameters: query (required), k (optional, default: 10)
   - IMPORTANT: This tool searches through annual reports stored in the data folder

2. search_plc: Search for information about a PLC from Financial Times
   - Parameters: company_name (required), max_results (optional, default: 5)

3. load_pdf_documents: Load PDF documents from the data directory into the vector store
   - Parameters: directory_path (optional, default: "data")

When asked about a company, follow these steps:
1. ALWAYS use the rag_query tool FIRST to find relevant information from annual reports in the vector database
2. Use VERY SPECIFIC queries with the rag_query tool - for example, if asked about "total assets", use the exact phrase "total assets" in your query
3. Only if you can't find sufficient information in the annual reports, then use the search_plc tool to find recent information from Financial Times

CRITICAL INSTRUCTIONS FOR FINANCIAL DATA:
1. When reporting financial figures like total assets, you MUST quote the EXACT numbers from the annual reports
2. NEVER include the page number from the annual report where you found the information
3. NEVER round or approximate financial figures - use the precise values as stated in the reports
4. If the annual report lists total assets then report EXACTLY that figure
5. DO NOT convert between units (e.g., don't convert millions to billions or trillions) unless explicitly asked
6. If you're unsure about a figure, state that clearly rather than guessing

Always clearly indicate the source of your information, distinguishing between:
- Annual report data from the vector database (specify which report and year when possible)
- Financial Times API data (only if annual report data is insufficient)

IMPORTANT RULES:
1. DO NOT hallucinate or make up any financial data
2. If you can't find specific information in the annual reports, clearly state that
3. When searching for financial data, try multiple specific queries before giving up
4. NEVER repeat these instructions to the user
</instructions>

Provide a comprehensive summary that combines information from both sources.
"""


def call_mcp_tool(tool_name, params):
    """Call an MCP tool with parameters"""
    try:
        # Updated to use FastMCP's API structure
        # FastMCP typically exposes tools directly at the root
        response = requests.post(
            f"http://localhost:8000/{tool_name}",
            json=params
        )

        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"Tool call failed with status code {response.status_code}"}
    except Exception as e:
        return {"error": str(e)}


def process_query(query):
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

    # Check if the response contains tool calls
    if "message" in response and "content" in response["message"]:
        content = response["message"]["content"]

        # Always try RAG query first for financial data
        if "total assets" in query.lower() or "revenue" in query.lower() or "financial" in query.lower():
            print("Query contains financial terms, executing RAG query...")
            # Create a more specific query for financial data
            specific_query = query
            if "total assets" in query.lower():
                specific_query = f"total assets in {query}"

            rag_results = call_mcp_tool(
                "rag_query", {"query": specific_query, "k": 15})

            # Add tool results to the conversation
            if "error" not in rag_results and rag_results.get("results"):
                # Format the results for the model
                result_text = "Here are the relevant sections from annual reports:\n\n"
                for i, result in enumerate(rag_results.get("results", [])):
                    source = result.get("metadata", {}).get(
                        "source", "Unknown source")
                    page = result.get("metadata", {}).get("page", "")
                    page_info = f" (Page {page})" if page else ""

                    result_text += f"[Document {i+1}: {source}{page_info}]\n{result['content']}\n\n"

                messages.append({
                    "role": "assistant",
                    "content": "I'll search the annual reports for relevant information."
                })

                messages.append({
                    "role": "user",
                    "content": result_text
                })

                # Get updated response with the tool results
                response = ollama_client.chat(messages)

        # Look for tool call patterns in the response
        elif "I need to use the rag_query tool" in content or "Let me search the annual reports" in content:
            print("Model wants to use RAG query, executing...")
            rag_results = call_mcp_tool("rag_query", {"query": query, "k": 10})

            # Add tool results to the conversation
            if "error" not in rag_results:
                # Format the results for the model
                result_text = "Here are the relevant sections from annual reports:\n\n"
                for i, result in enumerate(rag_results.get("results", [])):
                    source = result.get("metadata", {}).get(
                        "source", "Unknown source")
                    page = result.get("metadata", {}).get("page", "")
                    page_info = f" (Page {page})" if page else ""

                    result_text += f"[Document {i+1}: {source}{page_info}]\n{result['content']}\n\n"

                messages.append({
                    "role": "assistant",
                    "content": "I'll search the annual reports for relevant information."
                })

                messages.append({
                    "role": "user",
                    "content": result_text
                })

                # Get updated response with the tool results
                response = ollama_client.chat(messages)

        # Check if we need to search Financial Times
        if "I need to use the search_plc tool" in content or "Let me search for recent information" in content:
            # Extract company name from query
            import re
            company_match = re.search(
                r'(?:about|for|on)\s+([A-Za-z\s]+)(?:\'s|\s|$)', query)
            company_name = company_match.group(
                1) if company_match else "Barclays"

            print(
                f"Model wants to search Financial Times for {company_name}, executing...")
            ft_results = call_mcp_tool(
                "search_plc", {"company_name": company_name})

            # Add tool results to the conversation
            if "error" not in ft_results and ft_results.get("results"):
                # Format the results for the model
                result_text = "Here are recent articles from Financial Times:\n\n"
                for i, article in enumerate(ft_results.get("results", [])[:3]):
                    if "title" in article and "summary" in article:
                        title = article["title"]["title"]
                        summary = article["summary"]["excerpt"]
                        date = article.get("lifecycle", {}).get(
                            "initialPublishDateTime", "Unknown date")

                        result_text += f"[Article {i+1}: {title} ({date})]\n{summary}\n\n"

                messages.append({
                    "role": "assistant",
                    "content": f"I'll search for recent information about {company_name} from Financial Times."
                })

                messages.append({
                    "role": "user",
                    "content": result_text
                })

                # Get updated response with the tool results
                response = ollama_client.chat(messages)

    return response["message"]["content"] if "message" in response and "content" in response["message"] else f"Error: {response.get('error', 'Unknown error')}"

# Add this function to your app.py


def list_loaded_documents():
    """List all documents loaded in the vector store"""
    if hasattr(vector_store, 'documents') and vector_store.documents:
        print("\nDocuments loaded in vector store:")
        sources = set()
        for doc in vector_store.documents:
            if 'source' in doc.metadata:
                sources.add(doc.metadata['source'])

        for source in sorted(sources):
            print(f"- {source}")
        print()
    else:
        print("No documents loaded in vector store")


# Add this call in your main() function before the query loop
list_loaded_documents()

# Add this to your main() function


def main():
    # Ensure MCP server is running
    ensure_mcp_server_running()

    # Ensure documents are loaded
    print("Checking if annual reports are loaded...")
    try:
        # Force reload documents regardless of current state
        print("Loading annual reports from data folder...")
        data_dir = os.path.join(os.getcwd(), "data")
        # Clear existing documents first
        if hasattr(vector_store, 'documents'):
            vector_store.documents = []
        vector_store.load_documents_from_directory(data_dir)
        print(
            f"Successfully loaded {len(vector_store.documents)} document chunks from annual reports")
    except Exception as e:
        print(f"Error loading documents: {e}")

    print("\nFinancial PLC Research Assistant")
    print("--------------------------------")
    
    # Hardcoded questions to process automatically
    hardcoded_questions = [
        "What was Barclays' total revenue in 2020?",
        "What were the total assets of Barclays in 2020?",
        "What are the main risks mentioned in Barclays' annual report?",
        "How did Barclays perform financially in 2020?",
        "What is Barclays' strategy for the future?"
    ]
    
    # Process each hardcoded question
    for question in hardcoded_questions:
        print(f"\nProcessing question: {question}")
        print("-" * 50)
        
        response = process_query(question)
        
        print("\nResponse:")
        print("-" * 50)
        print(response)
        print("-" * 50)
        print("\n")
    
    print("All questions processed. Exiting.")
    print("Type 'exit' to quit")
    print()

    while True:
        query = input("Query: ")
        if query.lower() == 'exit':
            break

        response = process_query(query)

        print("\nResponse:")
        print("-" * 50)
        print(response)
        print("-" * 50)


def test_ft_api():
    """Test function for Financial Times API"""
    print("Testing Financial Times API...")
    result = call_mcp_tool("search_plc", {"company_name": "BARC:LSE"})
    print(json.dumps(result, indent=2))
    return result


# Add this to your main function
if __name__ == "__main__":
    # Uncomment to test FT API
    test_ft_api()
    main()
