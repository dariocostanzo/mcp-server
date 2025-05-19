import os
import json
from fastmcp import MCPServer, MCPTool
from src.tools.ft_api import FinancialTimesAPI
from src.rag.vector_store import VectorStore
import ollama
from dotenv import load_dotenv

load_dotenv()

# Initialize components
ft_api = FinancialTimesAPI()
vector_store = VectorStore()

# Load PDF documents from data directory on startup
data_dir = os.path.join(os.getcwd(), "data")
if os.path.exists(data_dir):
    print(f"Loading PDF documents from {data_dir}...")
    vector_store.load_documents_from_directory(data_dir)
    print("Documents loaded successfully!")
else:
    print(f"Data directory {data_dir} not found. No documents loaded.")

# Create MCP tools
class SearchPLCTool(MCPTool):
    name = "search_plc"
    description = "Search for information about a Public Limited Company (PLC) from Financial Times"
    
    def __init__(self):
        super().__init__()
        self.parameters = {
            "type": "object",
            "properties": {
                "company_name": {
                    "type": "string",
                    "description": "The name of the company to search for"
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of results to return",
                    "default": 5
                }
            },
            "required": ["company_name"]
        }
    
    async def execute(self, params):
        company_name = params.get("company_name")
        max_results = params.get("max_results", 5)
        
        results = ft_api.search_plc(company_name, max_results)
        
        # Add results to vector store for future RAG queries
        if "results" in results and len(results["results"]) > 0:
            documents = []
            for article in results["results"]:
                if "summary" in article and "title" in article:
                    documents.append({
                        "content": f"{article['title']['title']} - {article['summary']['excerpt']}",
                        "metadata": {
                            "id": article.get("id"),
                            "title": article["title"]["title"],
                            "published": article.get("lifecycle", {}).get("initialPublishDateTime")
                        }
                    })
            
            if documents:
                vector_store.add_documents(documents)
        
        return results

class RAGQueryTool(MCPTool):
    name = "rag_query"
    description = "Query the vector database for relevant information from annual reports"
    
    def __init__(self):
        super().__init__()
        self.parameters = {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The query to search for in the annual reports and other documents"
                },
                "k": {
                    "type": "integer",
                    "description": "Number of results to return",
                    "default": 5
                }
            },
            "required": ["query"]
        }
    
    async def execute(self, params):
        query = params.get("query")
        k = params.get("k", 5)
        
        results = vector_store.search(query, k)
        
        # Enhance results with source information
        for result in results:
            if 'metadata' in result and 'source' in result['metadata']:
                # Extract year from filename if possible
                source = result['metadata']['source']
                year = None
                
                # Try to extract year from filenames like "Company-Annual-Report-YYYY.pdf"
                import re
                year_match = re.search(r'(\d{4})', source)
                if year_match:
                    year = year_match.group(1)
                    
                if year:
                    result['metadata']['year'] = year
                    result['metadata']['source_description'] = f"Annual Report {year}"
                else:
                    result['metadata']['source_description'] = "Document"
        
        return {"results": results}

class LoadPDFDocumentsTool(MCPTool):
    name = "load_pdf_documents"
    description = "Load PDF documents from the data directory into the vector store"
    
    def __init__(self):
        super().__init__()
        self.parameters = {
            "type": "object",
            "properties": {
                "directory_path": {
                    "type": "string",
                    "description": "Path to the directory containing PDF files",
                    "default": "data"
                }
            }
        }
    
    async def execute(self, params):
        directory_path = params.get("directory_path", "data")
        
        # Make sure the path is absolute
        if not os.path.isabs(directory_path):
            directory_path = os.path.join(os.getcwd(), directory_path)
        
        # Load documents from the directory
        vector_store.load_documents_from_directory(directory_path)
        
        # Save the updated vector store
        os.makedirs("data", exist_ok=True)
        vector_store.save("data/index.faiss", "data/documents.pkl")
        
        return {"status": "success", "message": f"Documents loaded from {directory_path}"}

# Initialize MCP server
server = MCPServer()
server.add_tool(SearchPLCTool())
server.add_tool(RAGQueryTool())
server.add_tool(LoadPDFDocumentsTool())

# Start the server
if __name__ == "__main__":
    # Save vector store on exit
    import atexit
    
    def save_vector_store():
        os.makedirs("data", exist_ok=True)
        vector_store.save("data/index.faiss", "data/documents.pkl")
    
    atexit.register(save_vector_store)
    
    # Start the server
    server.start()