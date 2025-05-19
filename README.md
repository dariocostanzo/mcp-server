# MCP-RAG-Ollama Financial PLC Research Assistant

This project demonstrates how to build an application that:

- Uses the Model Context Protocol (MCP) for standardized communication
- Implements RAG (Retrieval-Augmented Generation) with a vector database
- Connects to Ollama for the LLM component
- Fetches information from the Financial Times API about PLCs (Public Limited Companies)

## Prerequisites

- Python 3.8+
- Ollama installed locally (https://ollama.ai/download)
- Financial Times API key

## Setup

1. Clone the repository
2. Install dependencies:

pip install -r requirements.txt

3. Create a `.env` file with your API keys:
```
FT_API_KEY=your_financial_times_api_key
OLLAMA_HOST= http://localhost:11434 
OLLAMA_MODEL=llama3
```
4. Make sure Ollama is installed and running

## Usage

1. Run the application:
   FT_API_KEY=your_financial_times_api_key
   OLLAMA_HOST= http://localhost:11434 OLLAMA_MODEL=llama3

2. Make sure Ollama is installed and running

## Usage

1. Run the application:

python app.py

2. Enter your query about a PLC (Public Limited Company)
3. The application will:

- Search for information using the Financial Times API
- Store the results in a vector database
- Use RAG to retrieve relevant information
- Generate a response using Ollama

## Project Structure

- `app.py`: Main application entry point
- `src/mcp_server.py`: MCP server implementation
- `src/ollama_client.py`: Client for interacting with Ollama
- `src/tools/ft_api.py`: Tool for interacting with the Financial Times API
- `src/rag/vector_store.py`: Vector database for RAG implementation

## How It Works

1. The user enters a query about a PLC
2. The application uses the MCP protocol to:

- Call the Financial Times API to search for information
- Retrieve shareholder information for companies using their ticker symbols
- Store the results in a vector database
- Query the vector database for relevant information

3. Ollama generates a response based on the retrieved information
4. The response is displayed to the user
