from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from retriever import get_retriever

def format_docs_with_citations(docs):
    """Formats retrieved chunks and explicitly embeds source metadata for the LLM."""
    formatted = []
    for doc in docs:
        source = doc.metadata.get("source_file", "Unknown Document")
        page = doc.metadata.get("page", "N/A")
        content = doc.page_content.replace('\n', ' ')
        formatted.append(f"[Doc: {source} | Page: {page}]\n{content}")
    return "\n\n---\n\n".join(formatted)
