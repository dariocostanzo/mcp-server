import os
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
import pickle
import json

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