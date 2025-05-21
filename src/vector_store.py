import os
import pickle
from typing import List, Dict, Any
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.document_loaders import PyPDFLoader

class VectorStore:
    """Simple vector store for document storage and retrieval using FAISS"""
    
    def __init__(self):
        """Initialize the vector store with HuggingFace embeddings"""
        self.embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        self.documents = []
        self.vectorstore = None
        
        # Try to load existing vector store if available
        try:
            self.load("data/index.faiss", "data/documents.pkl")
        except:
            print("No existing vector store found. Will create a new one.")
    
    def load_documents_from_directory(self, directory_path: str):
        """Load PDF documents from a directory"""
        if not os.path.exists(directory_path):
            print(f"Directory {directory_path} does not exist")
            return
        
        # Get all PDF files in the directory
        pdf_files = [os.path.join(directory_path, f) for f in os.listdir(directory_path) 
                    if f.lower().endswith('.pdf')]
        
        for file_path in pdf_files:
            try:
                print(f"Loading {file_path}...")
                loader = PyPDFLoader(file_path)
                documents = loader.load()
                
                # Split documents into chunks
                text_splitter = RecursiveCharacterTextSplitter(
                    chunk_size=500,
                    chunk_overlap=50
                )
                chunks = text_splitter.split_documents(documents)
                
                # Add source information
                for chunk in chunks:
                    chunk.metadata['source'] = os.path.basename(file_path)
                
                self.documents.extend(chunks)
                print(f"Added {len(chunks)} chunks from {os.path.basename(file_path)}")
            except Exception as e:
                print(f"Error loading {file_path}: {e}")
        
        # Create vector store
        self.create_vector_store()
        self.save("data/index.faiss", "data/documents.pkl")
    
    def create_vector_store(self):
        """Create a FAISS vector store from documents"""
        if not self.documents:
            print("No documents to create vector store from")
            return
            
        self.vectorstore = FAISS.from_documents(self.documents, self.embeddings)
    
    def search(self, query: str, k: int = 10):
        """Search the vector store for relevant documents"""
        if not self.vectorstore:
            print("Vector store not initialized")
            return []
        
        try:
            results = self.vectorstore.similarity_search_with_score(query, k=k)
            
            # Format results
            formatted_results = []
            for doc, score in results:
                formatted_results.append({
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                    "score": float(score)
                })
            
            return formatted_results
        except Exception as e:
            print(f"Error searching vector store: {e}")
            return []
    
    def save(self, index_path: str, documents_path: str):
        """Save the vector store and documents to disk"""
        if self.vectorstore:
            os.makedirs(os.path.dirname(index_path), exist_ok=True)
            self.vectorstore.save_local(index_path)
            with open(documents_path, 'wb') as f:
                pickle.dump(self.documents, f)
    
    def load(self, index_path: str, documents_path: str):
        """Load the vector store and documents from disk"""
        if not os.path.exists(index_path) or not os.path.exists(documents_path):
            raise FileNotFoundError("Vector store files not found")
        
        with open(documents_path, 'rb') as f:
            self.documents = pickle.load(f)
        
        self.vectorstore = FAISS.load_local(index_path, self.embeddings)
        print(f"Loaded {len(self.documents)} documents")