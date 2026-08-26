import os
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_classic.retrievers import ContextualCompressionRetriever
from langchain_community.document_compressors.flashrank_rerank import FlashrankRerank

def get_retriever():
    db_dir = os.getenv("CHROMA_PERSIST_DIR", "./db/chroma")
    
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    
    vectorstore = Chroma(
        collection_name="rag_collection",
        embedding_function=embeddings,
        persist_directory=db_dir
    )
    
    # Base retriever returning a broad set of candidates (k=15)
    base_retriever = vectorstore.as_retriever(search_kwargs={"k": 15})
    
    # FlashRank reranker compressing candidates down to the highly relevant top 4
    # Note: On first run, this downloads a tiny (~100MB) model to your local cache
    compressor = FlashrankRerank(model="ms-marco-MiniLM-L-12-v2", top_n=4)
    
    # Combine them into a single retrieval unit
    compression_retriever = ContextualCompressionRetriever(
        base_compressor=compressor,
        base_retriever=base_retriever
    )
    
    return compression_retriever