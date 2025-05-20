import os
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
from src.ft_api import FinancialTimesAPI
from src.vector_store import VectorStore

# Initialize components
ft_api = FinancialTimesAPI()
vector_store = VectorStore()

# Load documents on startup
data_dir = os.path.join(os.getcwd(), "data")
if os.path.exists(data_dir):
    print(f"Loading PDF documents from {data_dir}...")
    vector_store.load_documents_from_directory(data_dir)
    print("Documents loaded successfully!")
else:
    print(f"Data directory {data_dir} not found. No documents loaded.")

class MCPHandler(BaseHTTPRequestHandler):
    """Simple HTTP handler for MCP requests"""
    
    def _set_headers(self, content_type="application/json"):
        """Set response headers"""
        self.send_response(200)
        self.send_header('Content-type', content_type)
        self.end_headers()
    
    def do_GET(self):
        """Handle GET requests"""
        if self.path == "/health":
            self._set_headers()
            self.wfile.write(json.dumps({"status": "ok"}).encode())
        else:
            self._set_headers()
            self.wfile.write(json.dumps({"error": "Not found"}).encode())
    
    def do_POST(self):
        """Handle POST requests"""
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        
        try:
            data = json.loads(post_data.decode())
            
            # Process based on tool name
            if self.path == "/tools/search_plc":
                response = self._handle_search_plc(data)
            elif self.path == "/tools/rag_query":
                response = self._handle_rag_query(data)
            elif self.path == "/tools/load_pdf_documents":
                response = self._handle_load_pdf_documents(data)
            else:
                response = {"error": "Unknown tool"}
            
            self._set_headers()
            self.wfile.write(json.dumps(response).encode())
            
        except json.JSONDecodeError:
            self._set_headers()
            self.wfile.write(json.dumps({"error": "Invalid JSON"}).encode())
        except Exception as e:
            self._set_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())
    
    def _handle_search_plc(self, data):
        """Handle search_plc tool requests"""
        company_name = data.get("company_name")
        max_results = data.get("max_results", 5)
        
        if not company_name:
            return {"error": "company_name parameter is required"}
        
        return ft_api.search_plc(company_name, max_results)
    
    def _handle_rag_query(self, data):
        """Handle rag_query tool requests"""
        query = data.get("query")
        k = data.get("k", 10)  # Increased from 5 to 10
        
        if not query:
            return {"error": "query parameter is required"}
        
        # Enhance the query for financial information
        enhanced_query = query
        if "total assets" in query.lower():
            enhanced_query = f"{query} total assets balance sheet financial position"
        elif "revenue" in query.lower():
            enhanced_query = f"{query} revenue income statement profit"
            
        print(f"Enhanced query: {enhanced_query}")
        
        results = vector_store.search(enhanced_query, k)
        
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
    
    def _handle_load_pdf_documents(self, data):
        """Handle load_pdf_documents tool requests"""
        directory_path = data.get("directory_path", "data")
        
        # Make sure the path is absolute
        if not os.path.isabs(directory_path):
            directory_path = os.path.join(os.getcwd(), directory_path)
        
        # Load documents from the directory
        vector_store.load_documents_from_directory(directory_path)
        
        # Save the updated vector store
        os.makedirs("data", exist_ok=True)
        vector_store.save("data/index.faiss", "data/documents.pkl")
        
        return {"status": "success", "message": f"Documents loaded from {directory_path}"}

def run_server(port=8000):
    """Run the MCP server"""
    server_address = ('', port)
    httpd = HTTPServer(server_address, MCPHandler)
    print(f"Starting MCP server on port {port}...")
    httpd.serve_forever()

def start_server_thread():
    """Start the server in a separate thread"""
    server_thread = threading.Thread(target=run_server)
    server_thread.daemon = True
    server_thread.start()
    return server_thread

if __name__ == "__main__":
    # Save vector store on exit
    import atexit
    
    def save_vector_store():
        os.makedirs("data", exist_ok=True)
        vector_store.save("data/index.faiss", "data/documents.pkl")
    
    atexit.register(save_vector_store)
    
    # Start the server
    run_server()