print("🚀 Script started")


import os
import json
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SOURCE_DIRS = [
    os.path.join(BASE_DIR, "oracle_articles"),
    os.path.join(BASE_DIR, "baeldung_scraper", "baeldung_articles")
]
SOURCE_METADATA = {
    "Intro_to_Java.txt": {
        "url": "https://docs.oracle.com/javase/tutorial/java/concepts/index.html",
        "tags": ["java", "OOP", "oracle"]
    },
    "Java_Streams.txt": {
        "url": "https://www.baeldung.com/java-8-streams",
        "tags": ["java", "streams", "baeldung"]
    },
    # Add more entries as needed
}

print("📂 Resolved source directories:")
for path in SOURCE_DIRS:
    print("   -", path)

OUTPUT_DIR = "baeldung_scraper"


CHUNK_SIZE = 150
OVERLAP = 30

def chunk_text(text, max_words=CHUNK_SIZE, overlap=OVERLAP):
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        end = start + max_words
        chunk = ' '.join(words[start:end])
        chunks.append(chunk)
        start += max_words - overlap
    return chunks

def load_and_chunk_articles(source_dirs):
    all_chunks = []
    total_files = 0
    for folder in source_dirs:
        print(f"📁 Scanning folder: {folder}")
        if not os.path.exists(folder):
            print(f"❌ Folder not found: {folder}")
            continue
        for filename in os.listdir(folder):
            if filename.endswith(".txt"):
                total_files += 1
                print(f"🔍 Found file: {filename}")
    print(f"📦 Total .txt files found: {total_files}")

    for folder in source_dirs:
        print(f"📁 Scanning folder: {folder}")
        for filename in os.listdir(folder):
            if filename.endswith(".txt"):
                path = os.path.join(folder, filename)
                with open(path, "r", encoding="utf-8") as f:
                    text = f.read()
                    chunks = chunk_text(text)
                    print(f"📄 {filename}: {len(chunks)} chunks")
                    meta = SOURCE_METADATA.get(filename, {})
                    for i, chunk in enumerate(chunks):
                        all_chunks.append({
                            "text": chunk,
                            "source": filename,
                            "source_url": meta.get("url", ""),
                            "tags": meta.get("tags", []),
                            "chunk_index": i
                        })


    print(f"✅ Total chunks collected: {len(all_chunks)}")
    return all_chunks

def embed_chunks(chunks, model):
    texts = [chunk["text"] for chunk in chunks]
    return model.encode(texts)

def build_index(embeddings):
    dim = embeddings.shape[1]
    index = faiss.IndexFlatL2(dim)
    index.add(embeddings)
    return index

def save_rag_store(index, chunks, folder=OUTPUT_DIR):
    os.makedirs(folder, exist_ok=True)
    faiss.write_index(index, os.path.join(folder, "baeldung_index.faiss"))
    with open(os.path.join(folder, "chunks.json"), "w", encoding="utf-8") as f:
        json.dump(chunks, f, indent=2)
    print(f"✅ RAG store saved in folder: {folder}")
    
def main():
    print("🔍 Loading and chunking articles...")
    chunks = load_and_chunk_articles(SOURCE_DIRS)

    print("🧠 Embedding chunks...")
    model = SentenceTransformer('all-MiniLM-L6-v2')
    embeddings = embed_chunks(chunks, model)

    print("📦 Building FAISS index...")
    index = build_index(np.array(embeddings))

    print("💾 Saving RAG store...")
    save_rag_store(index, chunks)

    print("✅ RAG store built and saved.")

if __name__ == "__main__":
    main()
print("🚀 Script finished")