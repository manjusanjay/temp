import os
import chromadb
from sentence_transformers import SentenceTransformer

# Initialize embedding model and ChromaDB
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
chroma_client = chromadb.Client()
collection = chroma_client.create_collection(name="it_helpdesk")

def load_documents():
    """Load all documents from the documents folder into ChromaDB"""
    docs_path = os.path.join(os.path.dirname(__file__), 'documents')
    documents = []
    ids = []
    metadatas = []

    doc_id = 0
    for filename in os.listdir(docs_path):
        if filename.endswith('.txt'):
            filepath = os.path.join(docs_path, filename)
            with open(filepath, 'r') as f:
                content = f.read()

            # Split document into chunks by ISSUE blocks
            chunks = content.split('ISSUE:')
            for chunk in chunks:
                chunk = chunk.strip()
                if len(chunk) > 50:  # ignore very short chunks
                    documents.append(chunk)
                    ids.append(f"doc_{doc_id}")
                    metadatas.append({"source": filename})
                    doc_id += 1

    # Generate embeddings and store in ChromaDB
    embeddings = embedding_model.encode(documents).tolist()
    collection.add(
        documents=documents,
        embeddings=embeddings,
        ids=ids,
        metadatas=metadatas
    )
    print(f"Loaded {len(documents)} document chunks into vector database.")

def search(query, top_k=2):
    """Search vector DB for most relevant documents to the query"""
    query_embedding = embedding_model.encode([query]).tolist()
    results = collection.query(
        query_embeddings=query_embedding,
        n_results=top_k
    )

    retrieved = []
    for i in range(len(results['documents'][0])):
        retrieved.append({
            "content": results['documents'][0][i],
            "source": results['metadatas'][0][i]['source'],
            "distance": round(results['distances'][0][i], 4)
        })

    return retrieved

# Load documents when module is imported
load_documents()
