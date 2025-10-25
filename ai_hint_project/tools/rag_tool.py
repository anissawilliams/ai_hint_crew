from langchain.vectorstores import FAISS
from langchain.embeddings import HuggingFaceEmbeddings
import json

def build_rag_tool(index_path, chunks_path):
    # Load embedding model
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

    # Load FAISS vectorstore
    vectorstore = FAISS.load_local(index_path, embeddings)

    # Load original chunks (optional metadata)
    with open(chunks_path, "r") as f:
        chunks = json.load(f)

    # Wrap vectorstore in a callable function
    def rag_tool(query):
        docs = vectorstore.similarity_search(query, k=4)
        return "\n".join([doc.page_content for doc in docs])

    return rag_tool, chunks
