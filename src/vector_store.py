import os
import pickle
from typing import List, Dict, Any
import PyPDF2
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.document_loaders import PyPDFLoader

class VectorStore:
    """Simple vector store for document storage and retrieval"""
    
    def __init__(self):
        """Initialize the vector store with HuggingFace embeddings"""
        # Initialize embeddings model - using a small, efficient model
        self.embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        self.documents = []
        self.vector_store = None
        
        # Try to load existing vector store if available
        try:
            self.load("data/index.faiss", "data/documents.pkl")
            print("Loaded existing vector store")
        except:
            print("No existing vector store found, will create a new one when documents are added")
    
    def load_documents_from_directory(self, directory_path: str):
        """Load PDF documents from a directory"""
        if not os.path.exists(directory_path):
            print(f"Directory {directory_path} does not exist")
            return
        
        # Get all PDF files in the directory
        pdf_files = [f for f in os.listdir(directory_path) if f.lower().endswith('.pdf')]
        
        if not pdf_files:
            print(f"No PDF files found in {directory_path}")
            return
        
        all_docs = []
        
        # Process each PDF file
        for pdf_file in pdf_files:
            file_path = os.path.join(directory_path, pdf_file)
            print(f"Processing {file_path}...")
            
            try:
                # Use LangChain's PyPDFLoader
                loader = PyPDFLoader(file_path)
                documents = loader.load()
                
                # Split documents into smaller chunks for better retrieval
                text_splitter = RecursiveCharacterTextSplitter(
                    chunk_size=500,  # Smaller chunks for more precise retrieval
                    chunk_overlap=100,
                    separators=["\n\n", "\n", ".", "!", "?", ",", " ", ""]
                )
                chunks = text_splitter.split_documents(documents)
                
                # Add source information to metadata
                for chunk in chunks:
                    if 'source' not in chunk.metadata:
                        chunk.metadata['source'] = pdf_file
                    
                    # Make sure page numbers are included
                    if 'page' not in chunk.metadata and 'page_number' in chunk.metadata:
                        chunk.metadata['page'] = chunk.metadata['page_number']
                
                all_docs.extend(chunks)
                print(f"Added {len(chunks)} chunks from {pdf_file}")
                
            except Exception as e:
                print(f"Error processing {pdf_file}: {e}")
        
        # Add all documents to our list and vector store
        self.documents.extend(all_docs)
        
        # Create or update the vector store
        if self.vector_store is None:
            self.vector_store = FAISS.from_documents(all_docs, self.embeddings)
        else:
            self.vector_store.add_documents(all_docs)
        
        # Save the updated vector store
        self.save("data/index.faiss", "data/documents.pkl")
    
    def search(self, query: str, k: int = 10):  # Increased from 5 to 10
        """Search the vector store for relevant documents"""
        if self.vector_store is None:
            return []
        
        # Add specific financial terms to the query for better retrieval
        if "total assets" in query.lower():
            enhanced_query = f"{query} total assets balance sheet financial position"
        elif "revenue" in query.lower():
            enhanced_query = f"{query} revenue income statement profit"
        else:
            enhanced_query = query
            
        results = self.vector_store.similarity_search_with_score(enhanced_query, k=k)
        
        # Format results
        formatted_results = []
        for doc, score in results:
            formatted_results.append({
                "content": doc.page_content,
                "metadata": doc.metadata,
                "score": float(score)  # Convert numpy float to Python float
            })
        
        return formatted_results
    
    def save(self, index_path: str, documents_path: str):
        """Save the vector store and documents to disk"""
        if self.vector_store is not None:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(index_path), exist_ok=True)
            
            # Save the FAISS index
            self.vector_store.save_local(index_path)
            
            # Save the documents
            with open(documents_path, 'wb') as f:
                pickle.dump(self.documents, f)
            
            print(f"Vector store saved to {index_path} and {documents_path}")
    
    def load(self, index_path: str, documents_path: str):
        """Load the vector store and documents from disk"""
        if not os.path.exists(index_path) or not os.path.exists(documents_path):
            raise FileNotFoundError(f"Vector store files not found at {index_path} or {documents_path}")
        
        # Load the documents
        with open(documents_path, 'rb') as f:
            self.documents = pickle.load(f)
        
        # Load the FAISS index
        self.vector_store = FAISS.load_local(index_path, self.embeddings)
        
        print(f"Loaded {len(self.documents)} documents from {documents_path}")