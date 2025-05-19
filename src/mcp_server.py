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
    description = "Query the vector database for relevant information"
    
    def __init__(self):
        super().__init__()
        self.parameters = {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The query to search for in the vector database"
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
        return {"results": results}

class GetShareholdersTool(MCPTool):
    name = "get_shareholders"
    description = "Get major shareholders for a company using Financial Times API"
    
    def __init__(self):
        super().__init__()
        self.parameters = {
            "type": "object",
            "properties": {
                "ticker": {
                    "type": "string",
                    "description": "The ticker symbol in format SYMBOL:EXCHANGE (e.g., BARC:LSE for Barclays PLC)"
                }
            },
            "required": ["ticker"]
        }
    
    async def execute(self, params):
        ticker = params.get("ticker")
        shareholders = ft_api.get_shareholders(ticker)
        return {"shareholders": shareholders}

# Initialize MCP server
server = MCPServer()
server.add_tool(SearchPLCTool())
server.add_tool(RAGQueryTool())
server.add_tool(GetShareholdersTool())

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