from src.vector_store import VectorStore

# Initialize the vector store
vector_store = VectorStore()

# Load documents from the data directory
print("Loading documents from data folder...")
vector_store.load_documents_from_directory("data")
print("Documents loaded successfully!")

# The vector store automatically saves the updated index to:
# - data/index.faiss
# - data/documents.pkl