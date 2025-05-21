# Financial PLC Research Assistant

A simple RAG (Retrieval-Augmented Generation) application that extracts accurate financial information from annual reports using Mistral through Ollama.

## Features

- Uses Mistral model through Ollama for high-quality responses
- Implements RAG with LangChain components for document processing
- Provides a simple command-line interface for user queries
- Works on both Windows and macOS
- Focuses on accurate extraction of financial data from annual reports
- Connects to Financial Times API for enriched information

## Prerequisites

- Python 3.8+
- Ollama installed locally (https://ollama.ai/download)
- Annual reports in PDF format

## Setup

1. Install dependencies:

```bash
pip install -r requirements.txt

2. Create a .env file with your configuration:
```

```
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=mistral
FT_API_KEY=your_ft_api_key_here
```

3. Make sure Ollama is installed and running:

```
ollama pull mistral
```

4. Place your annual report PDFs in the data folder

## Usage

1. Run the application:

```
python app.py
```

2. Enter your query about financial information in the annual reports
3. The application will:
   - Search for relevant information in the annual reports
   - Generate a response using the Mistral model through Ollama
   - Provide accurate financial data from the annual reports

## Example Queries

- "What was Barclays PLC total assets value in 2020?"
- "How much revenue did Barclays report in 2019?"
- "What were the key financial highlights in the 2020 annual report?"

## Project Structure

- app.py : Main application with command-line interface
- src/ollama_client.py : Client for interacting with Ollama
- src/vector_store.py : LangChain-based vector store for document retrieval
- src/ft_api.py : Client for Financial Times API
- src/mcp_server.py : Simple MCP server implementation
