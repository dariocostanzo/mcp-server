import os
import json
import time
import re
import threading
import requests
from typing import Optional, List, Dict, Any, Union
from dotenv import load_dotenv
from fastmcp import FastMCP
from pydantic import BaseModel
from src.ft_api import FinancialTimesAPI
from src.vector_store import VectorStore

# Load environment variables
load_dotenv()

# Initialize components
ft_api = FinancialTimesAPI()
vector_store = VectorStore()

# Create FastMCP app
mcp = FastMCP("MCP RAG API")

# Load documents on startup
data_dir = os.path.join(os.getcwd(), "data")
if os.path.exists(data_dir):
    print(f"Loading PDF documents from {data_dir}...")
    vector_store.load_documents_from_directory(data_dir)
    print("Documents loaded successfully!")
else:
    print(f"Data directory {data_dir} not found. No documents loaded.")

# Define tool functions
@mcp.tool()
def health_check() -> Dict[str, str]:
    """Health check endpoint"""
    return {"status": "ok"}

@mcp.tool()
def search_plc(company_name: str, max_results: int = 5) -> Dict[str, Any]:
    """Search for a public limited company"""
    # Get the symbol for the company if available
    symbol = None
    if ":" in company_name:
        symbol = company_name
    elif company_name.lower() == "barclays":
        symbol = "BARC:LSE"
        
    # If we have a symbol, try to get detailed financial data
    if symbol:
        financial_data = fetch_ft_financial_data(symbol)
        if financial_data and "error" not in financial_data:
            return {
                "results": ft_api.search_plc(company_name, max_results),
                "financial_data": financial_data
            }
    
    # Fall back to regular search if detailed data not available
    return ft_api.search_plc(company_name, max_results)

def fetch_ft_financial_data(symbol: str) -> Dict[str, Any]:
    """Fetch financial data from Financial Times API"""
    try:
        # Get FT cookie from environment variable
        ft_cookie = os.getenv('FT_COOKIE', '')
        if not ft_cookie:
            print("Warning: FT_COOKIE not set in .env file")
            return {"error": "FT_COOKIE not configured"}
        
        # Common headers for FT API requests
        headers = {
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Language': 'en-GB,en;q=0.9',
            'Connection': 'keep-alive',
            'DNT': '1',
            'Referer': 'https://markets.ft.com/research/webservices/securities/v1/docs',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36 Edg/136.0.0.0',
            'X-FT-Source': 'f749296b753bb19e',
            'X-Requested-With': 'XMLHttpRequest',
            'sec-ch-ua': '"Chromium";v="136", "Microsoft Edge";v="136", "Not.A/Brand";v="99"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"'
        }
        
        # Set the cookie from environment variable
        cookies = {}
        for cookie_part in ft_cookie.split(';'):
            if '=' in cookie_part:
                name, value = cookie_part.strip().split('=', 1)
                cookies[name] = value
        
        # First, send tracking request to establish session
        tracking_url = 'https://spoor-api.ft.com/px.gif?type=component:view'
        tracking_data = {
            "system": {
                "api_key": "qUb9maKfKbtpRsdp0p2J7uWxRPGJEP",
                "version": "4.6.1",
                "source": "o-tracking",
                "transport": "xhr",
                "is_live": True
            },
            "context": {
                "product": "next",
                "app": "markets"
            },
            "device": {
                "spoor_id": cookies.get("spoor-id", "")
            }
        }
        
        requests.post(
            tracking_url,
            headers={**headers, 'Content-type': 'application/json'},
            json=tracking_data
        )
        
        # Generate timestamp for cache-busting
        timestamp = int(time.time() * 1000)
        
        # Collect data from multiple endpoints
        result_data = {}
        
        # 1. Get security details using the search endpoint
        if ":" in symbol:
            company_symbol = symbol.split(":")[0]
        else:
            company_symbol = symbol
            
        search_url = f'https://markets.ft.com/research/webservices/securities/v1/search?query={company_symbol}&_={timestamp}'
        search_response = requests.get(
            search_url,
            headers=headers,
            cookies=cookies
        )
        
        if search_response.status_code == 200:
            result_data["search"] = search_response.json()
        
        # 2. Get analyses data
        analyses_url = f'https://markets.ft.com/research/webservices/securities/v1/analyses?symbols={symbol}&_={timestamp}'
        analyses_response = requests.get(
            analyses_url,
            headers=headers,
            cookies=cookies
        )
        
        if analyses_response.status_code == 200:
            result_data["analyses"] = analyses_response.json()
        
        # 3. Get detailed data using the screen endpoint
        screen_data = {
            "symbols": symbol,
            "dataPoints": "symbol,name,sectorName,price,priceChange,percentChange,dayHigh,dayLow,marketCap,peRatio,dividend,dividendYield",
            "dataPacks": "details,spotQuote"
        }
        
        screen_url = f'https://markets.ft.com/research/webservices/securities/v1/screen?_={timestamp}'
        screen_response = requests.post(
            screen_url,
            headers={**headers, 'Content-type': 'application/json'},
            cookies=cookies,
            json=screen_data
        )
        
        if screen_response.status_code == 200:
            result_data["screen"] = screen_response.json()
        
        return result_data
            
    except Exception as e:
        print(f"Exception in FT API request: {str(e)}")
        return {"error": str(e)}

@mcp.tool()
def rag_query(query: str, k: int = 10) -> Dict[str, List[Dict[str, Any]]]:
    """Handle RAG query requests"""
    print(f"Query: {query}")
    
    results = vector_store.search(query, k)
    
    # Enhance results with source information
    for result in results:
        if 'metadata' in result and 'source' in result['metadata']:
            # Extract year from filename if possible
            source = result['metadata']['source']
            year = None
            
            # Try to extract year from filenames like "Company-Annual-Report-YYYY.pdf"
            year_match = re.search(r'(\d{4})', source)
            if year_match:
                year = year_match.group(1)
                
            if year:
                result['metadata']['year'] = year
                result['metadata']['source_description'] = f"Annual Report {year}"
            else:
                result['metadata']['source_description'] = "Document"
    
    return {"results": results}

@mcp.tool()
def load_pdf_documents(directory_path: str = "data") -> Dict[str, str]:
    """Handle load_pdf_documents tool requests"""
    # Make sure the path is absolute
    if not os.path.isabs(directory_path):
        directory_path = os.path.join(os.getcwd(), directory_path)
    
    # Load documents from the directory
    vector_store.load_documents_from_directory(directory_path)
    
    # Save the updated vector store
    save_vector_store()
    
    return {"status": "success", "message": f"Documents loaded from {directory_path}"}

def save_vector_store():
    """Save the vector store to disk"""
    os.makedirs("data", exist_ok=True)
    vector_store.save("data/index.faiss", "data/documents.pkl")

if __name__ == "__main__":
    # Save vector store on exit
    import atexit
    atexit.register(save_vector_store)
    
    # Start the MCP server
    mcp.run()