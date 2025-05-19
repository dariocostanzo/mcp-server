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

```bash
pip install -r requirements.txt
```

3. Create a `.env` file with your API keys:

```
FT_API_KEY=your_financial_times_api_key
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama3
```

4. Make sure Ollama is installed and running:

```bash
ollama pull llama3
```

## Usage

1. Run the application:

```bash
python app.py
```

2. Enter your query about a PLC (Public Limited Company)
3. The application will:

- First search for information in annual reports using RAG
- If needed, search for additional information using the Financial Times API
- Generate a response using Ollama
- Provide accurate financial data from the annual reports

## Project Structure

- `app.py`: Main application entry point
- `src/mcp_server.py`: MCP server implementation
- `src/ollama_client.py`: Client for interacting with Ollama
- `src/tools/ft_api.py`: Tool for interacting with the Financial Times API
- `src/rag/vector_store.py`: Vector database for RAG implementation

## How It Works

1. The user enters a query about a PLC
2. The application uses the MCP protocol to:

   - First query the vector database for relevant information from annual reports in the data folder
   - Only if necessary, call the Financial Times API to search for additional information
   - Combine information from both sources to provide a comprehensive response

3. Ollama generates a response based on the retrieved information
4. The response is displayed to the user

## Important Notes

- The application prioritizes information from annual reports stored in the data folder
- For financial metrics like total assets, the application uses exact figures from the annual reports
- The application will not provide shareholder information

## Example Queries

- "What was Barclays' total assets value in 2020?"
- "What was Barclays' total assets value in 2021?"
- "What was Barclays' total assets value in 2022?"
- "What were Barclays' revenue figures for 2021?"
- "How did Barclays' financial performance change from 2020 to 2022?"

## Troubleshooting

If you encounter issues with the application not finding documents in the data folder:

- Verify that your PDF files are in the correct location: `/data/` folder in the project root
- Check the console output for any error messages during document loading
- Try using more specific queries that might match the content in your annual reports
