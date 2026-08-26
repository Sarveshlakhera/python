from langchain_openai import ChatOpenAI
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

def create_rag_pipeline():
    retriever = get_retriever()
    
    # Use a token-efficient, fast model for generation
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    
    system_prompt = """You are an expert, precise AI assistant for answering questions based ONLY on the provided context.
    
    Context Documents:
    {context}
    
    Instructions:
    1. Answer the question using ONLY facts found in the provided context documents.
    2. Do NOT use outside knowledge or hallucinate.
    3. If the context does not contain the answer, reply exactly with: "I could not find relevant information in the provided documents."
    4. Provide inline citations citing the source document using the format: [Doc: filename.pdf, Page: X].
    
    Question: {question}
    """
    
    prompt = ChatPromptTemplate.from_template(system_prompt)
    
    # LangChain Expression Language (LCEL) chain
    rag_chain = (
        {"context": retriever | format_docs_with_citations, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )
    
    return rag_chain