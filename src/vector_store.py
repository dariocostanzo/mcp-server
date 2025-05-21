import os
import pickle
import re
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

                # Extract filename and year information
                filename = os.path.basename(file_path)

                # Add enhanced metadata to each chunk
                for chunk in chunks:
                    # Add basic source information
                    chunk.metadata['source'] = filename

                    # Extract company name and year if possible
                    company_name = None
                    year = None

                    # Try to extract year from filename (e.g., "Company-Annual-Report-2020.pdf")
                    year_match = re.search(r'(\d{4})', filename)
                    if year_match:
                        year = year_match.group(1)

                    # Try to extract company name from filename
                    # Common patterns: "Company-PLC", "Company_plc", etc.
                    company_match = re.search(r'^([A-Za-z\-]+)', filename)
                    if company_match:
                        company_name = company_match.group(1).replace('-', ' ')

                    # Add extracted information to metadata
                    if year:
                        chunk.metadata['year'] = year
                    if company_name:
                        chunk.metadata['company'] = company_name

                    # Create a readable source description
                    source_desc = filename
                    if company_name and year:
                        source_desc = f"{company_name} Annual Report {year}"
                    elif year:
                        source_desc = f"Annual Report {year}"

                    chunk.metadata['source_description'] = source_desc

                self.documents.extend(chunks)
                print(f"Added {len(chunks)} chunks from {filename}")
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

        self.vectorstore = FAISS.from_documents(
            self.documents, self.embeddings)

    def search(self, query: str, k: int = 10):
        """Search the vector store for relevant documents"""
        if not self.vectorstore:
            print("Vector store not initialized")
            return []
        print("<---- Search the vector store for relevant documents ---->")
        try:
            results = self.vectorstore.similarity_search_with_score(query, k=k)
            print(
                "<---- Search the vector store for relevant documents - results ---->", results)

            # Format results with enhanced metadata
            formatted_results = []
            for doc, score in results:
                result = {
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                    "score": float(score)
                }

                # Add a formatted source field for easier display
                if 'source_description' in doc.metadata:
                    result['source'] = doc.metadata['source_description']
                elif 'year' in doc.metadata:
                    result['source'] = f"Annual Report {doc.metadata['year']}"
                else:
                    result['source'] = doc.metadata.get(
                        'source', 'Unknown source')

                formatted_results.append(result)
            print('query', query, 'formatted results', formatted_results)
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
