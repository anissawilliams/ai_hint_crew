
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from chromadb.config import Settings

import json
import streamlit as st

def build_rag_tool(index_path, chunks_path):
    # Use OpenAI embeddings for simplicity and Streamlit compatibility
    embeddings = OpenAIEmbeddings(api_key=st.secrets["OPENAI_API_KEY"])

    # Load Chroma vectorstore from disk

   vectorstore = Chroma.from_persistent_index(
    embedding_function=embeddings,
    persist_directory=index_path
   )


    # Load original chunks (optional metadata)
    with open(chunks_path, "r") as f:
        chunks = json.load(f)

    # Wrap vectorstore in a callable function
    def rag_tool(query):
        docs = vectorstore.similarity_search(query, k=4)
        return "\n".join([doc.page_content for doc in docs])

    return rag_tool, chunks
