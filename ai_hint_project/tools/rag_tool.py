import os
import json
import streamlit as st
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS, Chroma

def build_rag_tool(index_path, chunks_path):
    embeddings = OpenAIEmbeddings(api_key=st.secrets["OPENAI_API_KEY"])

    vectorstore = None
    try:
        vectorstore = Chroma(
            persist_directory=index_path,
            embedding_function=embeddings
        )
        print("✅ Loaded Chroma index")
    except Exception as e:
        print(f"⚠️ Chroma load failed: {e}")
        try:
            vectorstore = FAISS.load_local(
                folder_path=index_path,
                embeddings=embeddings
            )

            print("✅ Fallback to FAISS index")
        except Exception as e2:
            print(f"❌ FAISS load failed: {e2}")
            raise RuntimeError("No valid vectorstore found")

    with open(chunks_path, "r") as f:
        chunks = json.load(f)

    def rag_tool(query):
        docs = vectorstore.similarity_search(query, k=4)
        return "\n".join([doc.page_content for doc in docs])

    return rag_tool, chunks
