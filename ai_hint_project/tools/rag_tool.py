import json
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer

def load_rag_store(folder="baeldung_scraper"):
    index = faiss.read_index(f"{folder}/baeldung_index.faiss")
    with open(f"{folder}/chunks.json", "r", encoding="utf-8") as f:
        chunks = json.load(f)
    return index, chunks

def build_rag_tool(index_path, chunks_path):
    index = faiss.read_index(index_path)
    with open(chunks_path, "r", encoding="utf-8") as f:
        chunks = json.load(f)
    return index, chunks


def search(query, model, index, chunks, top_k=5):
    query_embedding = model.encode([query])
    distances, indices = index.search(np.array(query_embedding), top_k)
    return [chunks[i] for i in indices[0]]

if __name__ == "__main__":
    model = SentenceTransformer('all-MiniLM-L6-v2')
    index, chunks = load_rag_store()

    query = "How do Java streams work?"
    results = search(query, model, index, chunks)

    print("\n🔎 Top Results:")
    for i, result in enumerate(results):
        print(f"\nResult {i+1}:\n{result[:500]}")
