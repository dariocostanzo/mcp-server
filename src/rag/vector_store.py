import os
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
import pickle
import json
from PyPDF2 import PdfReader
import glob

class VectorStore:
    def __init__(self, model_name="all-MiniLM-L6-v2", index_path=None, data_path=None):
        """
        Initialize the vector store with a sentence transformer model
        """
        self.model = SentenceTransformer(model_name)
        self.dimension = self.model.get_sentence_embedding_dimension()
        
        # Create or load FAISS index
        if index_path and os.path.exists(index_path):
            self.index = faiss.read_index(index_path)
            with open(data_path, 'rb') as f:
                self.documents = pickle.load(f)
        else:
            self.index = faiss.IndexFlatL2(self.dimension)
            self.documents = []
    
    def add_documents(self, documents):
        """
        Add documents to the vector store
        
        Args:
            documents: List of dictionaries with 'content' and 'metadata' keys
        """
        contents = [doc['content'] for doc in documents]
        embeddings = self.model.encode(contents)
        
        # Add to FAISS index
        self.index.add(np.array(embeddings).astype('float32'))
        
        # Store documents
        start_idx = len(self.documents)
        for i, doc in enumerate(documents):
            doc['id'] = start_idx + i
            self.documents.append(doc)
    
    def search(self, query, k=5):
        """
        Search for similar documents
        
        Args:
            query: The search query
            k: Number of results to return
        
        Returns:
            List of documents with similarity scores
        """
        query_embedding = self.model.encode([query])
        scores, indices = self.index.search(np.array(query_embedding).astype('float32'), k)
        
        results = []
        for i, idx in enumerate(indices[0]):
            if idx < len(self.documents) and idx >= 0:
                doc = self.documents[idx].copy()
                doc['score'] = float(scores[0][i])
                results.append(doc)
        
        return results
    
    def save(self, index_path, data_path):
        """
        Save the index and documents to disk
        """
        faiss.write_index(self.index, index_path)
        with open(data_path, 'wb') as f:
            pickle.dump(self.documents, f)
    
    def load_pdf_documents(self, pdf_path):
        """
        Load and process a PDF document
        
        Args:
            pdf_path: Path to the PDF file
        
        Returns:
            List of document chunks with metadata
        """
        print(f"Processing PDF: {pdf_path}")
        documents = []
        
        try:
            # Extract the filename for metadata
            filename = os.path.basename(pdf_path)
            
            # Try to extract company name and year from filename
            import re
            company_match = re.search(r'^([A-Za-z\-]+)', filename)
            year_match = re.search(r'(\d{4})', filename)
            
            company_name = company_match.group(1).replace('-', ' ') if company_match else "Unknown"
            year = year_match.group(1) if year_match else "Unknown"
            
            # Read the PDF
            reader = PdfReader(pdf_path)
            
            # Process each page
            for i, page in enumerate(reader.pages):
                text = page.extract_text()
                
                # Skip empty pages
                if not text.strip():
                    continue
                
                # Create chunks of text (simple approach: one page = one chunk)
                documents.append({
                    'content': text,
                    'metadata': {
                        'source': filename,
                        'company': company_name,
                        'year': year,
                        'page': i + 1,
                        'total_pages': len(reader.pages),
                        'document_type': 'Annual Report'
                    }
                })
                
        except Exception as e:
            print(f"Error processing PDF {pdf_path}: {e}")
        
        return documents
    
    def load_documents_from_directory(self, directory_path):
        """
        Load all PDF documents from a directory
        
        Args:
            directory_path: Path to the directory containing PDF files
        """
        # Find all PDF files in the directory
        pdf_files = glob.glob(os.path.join(directory_path, "*.pdf"))
        
        if not pdf_files:
            print(f"No PDF files found in {directory_path}")
            return
        
        print(f"Found {len(pdf_files)} PDF files in {directory_path}")
        
        # Process each PDF file
        for pdf_file in pdf_files:
            documents = self.load_pdf_documents(pdf_file)
            if documents:
                print(f"Adding {len(documents)} chunks from {pdf_file}")
                self.add_documents(documents)
            else:
                print(f"No content extracted from {pdf_file}")