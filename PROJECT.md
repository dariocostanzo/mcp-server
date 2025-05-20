# Financial PLC Research Assistant: Project Analysis 
This application is a financial research assistant that uses RAG (Retrieval-Augmented Generation) with Ollama to provide accurate information about Public Limited Companies (PLCs) from annual reports and Financial Times data. Let me break down how it works file by file and function by function. 

## Project Overview 
The application combines: 

1. RAG (Retrieval-Augmented Generation) for finding relevant information in annual reports 
2. Ollama for running the Mistral LLM locally 
3. MCP (Model Context Protocol) for tool-calling capabilities 
4. Financial Times API integration for up-to-date financial information 

## File-by-File Analysis 
### 1. app.py - Main Application 
This is the entry point of the application with these key functions: 

- `ensure_mcp_server_running()`: Checks if the MCP server is running and starts it if not 
- `call_mcp_tool(tool_name, params)`: Makes HTTP requests to the MCP server to call specific tools 
- `process_query(query)`: The core function that: 
  - Creates a chat message with system prompt and user query 
  - Sends it to Ollama 
  - Analyzes the response for tool call patterns 
  - Executes RAG queries for financial data 
  - Searches Financial Times if needed 
  - Returns the final response 
- `main()`: Runs the command-line interface for user interaction 
- `test_ft_api()`: A utility function to test the Financial Times API 

### 2. src/mcp_server.py - MCP Server Implementation 
This file implements a simple HTTP server that provides tool functionality: 

- `MCPHandler` class: Handles HTTP requests with these methods: 
  - `_set_headers()`: Sets response headers 
  - `do_GET()`: Handles GET requests (health check) 
  - `do_POST()`: Handles POST requests for tool calls 
  - `_handle_search_plc()`: Searches for PLC information via Financial Times API 
  - `_fetch_ft_financial_data()`: Fetches detailed financial data from FT API 
  - `_handle_rag_query()`: Performs RAG queries on the vector database 
  - `_handle_load_pdf_documents()`: Loads PDF documents into the vector store 

### 3. src/ollama_client.py - Ollama Integration 
Handles interaction with the Ollama API: 

- `OllamaClient` class: 
  - `__init__()`: Initializes with model and host configuration 
  - `ensure_ollama_running()`: Checks if Ollama is running and starts it if not 
  - `chat()`: Sends chat requests to Ollama 

### 4. src/vector_store.py (inferred from context) 
Manages the vector database for RAG: 

- `VectorStore` class (inferred): 
  - `load_documents_from_directory()`: Loads PDF documents from a directory 
  - `search()`: Searches the vector database for relevant information 
  - `save()`: Saves the vector store to disk 

### 5. src/ft_api.py (inferred from context) 
Handles Financial Times API integration: 

- `FinancialTimesAPI` class (inferred): 
  - `search_plc()`: Searches for PLC information 

### 6. .env File 
Contains environment variables: 

- `OLLAMA_HOST`: URL for Ollama server 
- `OLLAMA_MODEL`: Model to use (mistral) 
- `FT_COOKIE`: Authentication cookie for Financial Times API 

## How MCP Works with RAG 
The Model Context Protocol (MCP) in this application is a custom implementation that allows the LLM to use tools. Here's how it works with RAG: 

1. **MCP Server Setup**: 
   
   - The application starts an HTTP server (`mcp_server.py`) that exposes endpoints for tool calls 
   - Tools are exposed as HTTP endpoints (e.g., `/tools/rag_query`, `/tools/search_plc`) 

2. **Tool Calling Process**: 
   
   - When the user asks a question, the system prompt instructs the model about available tools 
   - The model's response is analyzed for tool call patterns (e.g., "I need to use the rag_query tool") 
   - The application then calls the appropriate MCP tool via HTTP 

3. **RAG Implementation**: 
   
   - The `rag_query` tool searches the vector database for relevant information 
   - PDF documents (annual reports) are loaded into a vector store 
   - When a query is made, the system: 
     - Enhances the query for financial information 
     - Retrieves relevant document chunks 
     - Adds source information (including year and page numbers) 
     - Returns the results to be incorporated into the model's context 

4. **Integration Flow**: 
   
   - User query → Ollama → Response analysis → MCP tool call → RAG search → Results added to context → Final response 

5. **Financial Data Enhancement**: 
   
   - For financial queries, the system automatically enhances the query (e.g., adding "balance sheet" to "total assets" queries) 
   - The Financial Times API is used as a fallback when annual report data is insufficient 

## Key Features 
1. **Automatic Document Loading**: Loads PDF documents from the data directory on startup 
2. **Query Enhancement**: Automatically enhances financial queries for better retrieval 
3. **Source Attribution**: Includes source information (document, year, page) with retrieved information 
4. **Financial Times Integration**: Provides up-to-date financial information when needed 
5. **Local LLM Execution**: Uses Ollama to run the Mistral model locally 

This application demonstrates a practical implementation of RAG with a local LLM, showing how to combine document retrieval with model generation to provide accurate financial information from annual reports.