from langchain.document_loaders import DirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import FAISS
import os
import asyncio

async def indexKB():
    try:
        loader = DirectoryLoader('pkm', glob="**/*.md")
        documents = loader.load()
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        texts = text_splitter.split_documents(documents)
        embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        vectorstore = FAISS.from_documents(texts, embeddings)
        vectorstore.save_local("pkm_index")
        print("Indexed PKM to pkm_index")
    except Exception as e:
        print(f"Indexing failed: {e}")

async def searchKB(query):
    try:
        embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        vectorstore = FAISS.load_local("pkm_index", embeddings)
        docs = vectorstore.similarity_search(query, k=3)
        return "\n".join([doc.page_content for doc in docs])
    except Exception as e:
        return f"Search failed: {e}"