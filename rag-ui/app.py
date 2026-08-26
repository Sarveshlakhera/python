import os
import shutil
import re
import streamlit as st
import streamlit.components.v1 as components
from pathlib import Path
from dotenv import load_dotenv

# Set UI Configuration first
st.set_page_config(page_title="Nexus | Enterprise RAG", page_icon="✨", layout="wide")

# ------------------------------------------------------
# 2026 Modern SaaS UI Theme (Glassmorphism & Minimalism)
# ------------------------------------------------------
def apply_custom_theme():
    st.markdown("""
    <style>
        /* 1. Import a hyper-modern, highly legible geometric font */
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap');

        html, body, [class*="css"], .stTextInput > label, .stSelectbox > label, .stMarkdown {
            font-family: 'Outfit', sans-serif !important;
        }

        /* 2. Hide standard Streamlit chrome for a native-app feel */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {background-color: transparent !important;}

        /* 3. The Canvas: Subtle ambient background */
        .stApp {
            background-color: #fafbfc;
            background-image: radial-gradient(circle at 10% 20%, rgba(240, 242, 250, 1) 0%, rgba(255, 255, 255, 1) 90%);
        }

        /* 4. The Sidebar: Liquid Glass (Glassmorphism) */
        [data-testid="stSidebar"] {
            background: rgba(255, 255, 255, 0.6) !important;
            backdrop-filter: blur(20px) !important;
            -webkit-backdrop-filter: blur(20px) !important;
            border-right: 1px solid rgba(0, 0, 0, 0.04) !important;
        }

        /* 5. Main Title: Elegantly subdued, premium gradient */
        h1 {
            font-weight: 700 !important;
            letter-spacing: -1px;
            background: linear-gradient(135deg, #18181b 0%, #71717a 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 1rem !important;
        }

        /* 6. Chat Interface: Bento-style Floating Cards */
        [data-testid="stChatMessage"] {
            background: #ffffff;
            border: 1px solid rgba(0, 0, 0, 0.03);
            border-radius: 18px;
            padding: 1.5rem;
            box-shadow: 0 4px 16px rgba(0,0,0,0.02);
            margin-bottom: 1.2rem;
            transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1), box-shadow 0.3s ease;
        }
        
        [data-testid="stChatMessage"]:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 24px rgba(0,0,0,0.05);
        }

        /* Avatar tuning */
        [data-testid="chatAvatarIcon-user"] { background-color: #18181b; }
        [data-testid="chatAvatarIcon-assistant"] { background-color: #3b82f6; }

        /* 7. Chat Input Bar: Frosted floating pill */
        .stChatInputContainer {
            border-radius: 24px !important;
            box-shadow: 0 8px 30px rgba(0,0,0,0.06) !important;
            border: 1px solid rgba(255, 255, 255, 0.8) !important;
            background: rgba(255, 255, 255, 0.85) !important;
            backdrop-filter: blur(12px) !important;
            padding: 0.2rem 1rem !important;
        }

        /* 8. Buttons: Soft tactile microinteractions */
        .stButton>button {
            border-radius: 12px !important;
            border: 1px solid rgba(0,0,0,0.06) !important;
            background: #ffffff !important;
            font-weight: 500 !important;
            color: #27272a !important;
            transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1) !important;
            box-shadow: 0 2px 4px rgba(0,0,0,0.02) !important;
        }

        .stButton>button:hover {
            background: #18181b !important;
            color: #ffffff !important;
            transform: translateY(-2px) !important;
            box-shadow: 0 8px 16px rgba(0,0,0,0.1) !important;
        }

        /* Primary Button (Upload / Action buttons) */
        .stButton>button[kind="primary"] {
            background: linear-gradient(135deg, #2563eb, #3b82f6) !important;
            color: #ffffff !important;
            border: none !important;
        }
        .stButton>button[kind="primary"]:hover {
            transform: translateY(-2px) !important;
            box-shadow: 0 8px 20px rgba(59, 130, 246, 0.3) !important;
        }

        /* 9. Expanders & Status boxes */
        [data-testid="stExpander"] {
            border: 1px solid rgba(0,0,0,0.04);
            border-radius: 12px;
            background: #fafafa;
        }
        .streamlit-expanderHeader {
            font-weight: 500 !important;
            color: #52525b !important;
        }
    </style>
    """, unsafe_allow_html=True)

# Call the theme function immediately
apply_custom_theme()

from ingest import build_index
from retriever import get_retriever
from pipeline import format_docs_with_citations
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

load_dotenv()

DATA_DIR = os.getenv("DATA_DIR", "./data/input_docs")
DB_DIR = os.getenv("CHROMA_PERSIST_DIR", "./db/chroma")
os.makedirs(DATA_DIR, exist_ok=True)

# ------------------------------------------------------
# Helper Functions
# ------------------------------------------------------
def render_mermaid(code: str):
    """Takes Mermaid.js code and renders it as an HTML graphic in Streamlit."""
    components.html(
        f"""
        <div class="mermaid" style="display: flex; justify-content: center; background-color: transparent; padding: 20px; border-radius: 10px;">
            {code}
        </div>
        <script type="module">
            import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
            mermaid.initialize({{ startOnLoad: true, theme: 'default' }});
        </script>
        """,
        height=450, scrolling=True
    )

def extract_and_render_visuals(text: str):
    """Scans the LLM's response for Mermaid code blocks and renders them."""
    mermaid_blocks = re.findall(r'```mermaid\n(.*?)\n```', text, re.DOTALL)
    for block in mermaid_blocks:
        render_mermaid(block)

def generate_chat_transcript(messages):
    transcript = "Nexus RAG Assistant - Chat Transcript\n"
    transcript += "="*50 + "\n\n"
    
    for msg in messages:
        sender = "You" if msg["role"] == "user" else "Nexus Assistant"
        transcript += f"{sender}:\n{msg['content']}\n"
        
        if "sources" in msg and msg["sources"]:
            transcript += "\n[Sources Cited]:\n"
            for idx, doc in enumerate(msg["sources"]):
                source_name = doc.metadata.get('source_file', 'Unknown')
                page = doc.metadata.get('page', 'N/A')
                transcript += f"  - {idx+1}. {source_name} (Page: {page})\n"
                
        transcript += "\n" + "-"*50 + "\n\n"
    return transcript

def clear_knowledge_base():
    for file in Path(DATA_DIR).rglob("*.*"):
        os.remove(file)
    if os.path.exists(DB_DIR):
        shutil.rmtree(DB_DIR)
    build_index() 

def delete_individual_file(filename):
    file_path = os.path.join(DATA_DIR, filename)
    if os.path.exists(file_path):
        os.remove(file_path)
        build_index()

# ------------------------------------------------------
# 1. Sidebar: Authentication & Document Management
# ------------------------------------------------------
with st.sidebar:
    st.header("🔑 Authentication")
    
    if "api_key" in st.session_state and st.session_state.api_key:
        st.success("API Key securely loaded")
        
        if "messages" in st.session_state and len(st.session_state.messages) > 1:
            chat_transcript = generate_chat_transcript(st.session_state.messages)
            st.download_button("💾 Download Chat History", data=chat_transcript, file_name="nexus_chat_history.txt", mime="text/plain", use_container_width=True)
            
        st.write("") 
        
        if st.button("🚪 Logout / Clear Session", type="primary", use_container_width=True):
            st.session_state.clear()  
            st.rerun()                
            
    else:
        user_api_key = st.text_input("Enter your Google Gemini API Key", type="password", help="Get a free key at https://aistudio.google.com/")
        if user_api_key:
            st.session_state.api_key = user_api_key
            st.rerun() 
        else:
            st.warning("Please enter an API Key to enable chat.")
            
    st.divider()
    
    st.header("🗂️ Knowledge Base")
    
    uploaded_files = st.file_uploader("Upload new documents:", accept_multiple_files=True, type=['pdf', 'docx', 'txt', 'csv'])
    
    if st.button("Upload & Index", type="primary", use_container_width=True):
        if uploaded_files:
            with st.status("Ingesting Documents...", expanded=True) as status:
                st.write("💾 Saving files locally...")
                for file in uploaded_files:
                    file_path = os.path.join(DATA_DIR, file.name)
                    with open(file_path, "wb") as f:
                        f.write(file.getbuffer())
                st.write("🧠 Hashing and updating ChromaDB...")
                build_index() 
                status.update(label="Index updated successfully!", state="complete", expanded=False)
            st.success("Knowledge base is up to date.")
            st.rerun() 
        else:
            st.warning("Please select files to upload first.")

    st.divider()

    st.markdown("### 📄 Active Documents")
    active_files = list(Path(DATA_DIR).rglob("*.*"))
    st.metric("Total Documents", len(active_files))
    
    if active_files:
        st.write("Manage your uploaded files below:")
        for file_path in active_files:
            col1, col2 = st.columns([0.85, 0.15])
            with col1:
                st.markdown(f"📄 `{file_path.name}`")
            with col2:
                if st.button("❌", key=f"del_{file_path.name}", help=f"Delete {file_path.name}"):
                    with st.spinner(f"Deleting {file_path.name}..."):
                        delete_individual_file(file_path.name)
                    st.success("Deleted!")
                    st.rerun()
    else:
        st.info("No documents currently in the knowledge base.")

    st.divider()

    st.markdown("### ⚠️ Danger Zone")
    if st.button("🗑️ Clear Entire Knowledge Base", type="primary", use_container_width=True):
        with st.spinner("Deleting all files and wiping the database..."):
            clear_knowledge_base()
            if "messages" in st.session_state:
                st.session_state.messages = [{"role": "assistant", "content": "Knowledge base completely wiped. Upload new documents to begin."}]
        st.success("Knowledge base cleared.")
        st.rerun()

# ------------------------------------------------------
# 2. Main Window: Chat Interface
# ------------------------------------------------------
st.title("✨ Nexus RAG Assistant")
st.markdown("Ask questions based on your ingested documents. The assistant provides inline citations.")

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hello! I am ready to answer questions based on your documents. What would you like to know?"}
    ]

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        
        # Check and render any visuals that were generated in the past conversation
        if msg["role"] == "assistant":
            extract_and_render_visuals(msg["content"])
            
        if "sources" in msg and msg["sources"]:
            with st.expander("📚 View Source Documents"):
                for idx, doc in enumerate(msg["sources"]):
                    source_name = doc.metadata.get('source_file', 'Unknown')
                    page = doc.metadata.get('page', 'N/A')
                    st.markdown(f"**{idx+1}. {source_name}** (Page: {page})")
                    st.caption(doc.page_content.replace('\n', ' ')[:300] + "...")

# ------------------------------------------------------
# 3. Query Processing & Response Generation
# ------------------------------------------------------
chat_disabled = "api_key" not in st.session_state or not st.session_state.api_key

if query := st.chat_input("Ask a question about your documents...", disabled=chat_disabled):
    
    st.session_state.messages.append({"role": "user", "content": query})
    with st.chat_message("user"):
        st.markdown(query)
        
    with st.chat_message("assistant"):
        with st.status("Searching knowledge base...", expanded=True) as status:
            st.write("🔎 Fetching candidates from ChromaDB...")
            retriever = get_retriever()
            
            st.write("⚡ Reranking context with FlashRank...")
            docs = retriever.invoke(query)
            status.update(label=f"Retrieved {len(docs)} highly relevant chunks.", state="complete", expanded=False)
            
        if docs:
            with st.expander(f"📚 View {len(docs)} Source Documents"):
                for idx, doc in enumerate(docs):
                    source_name = doc.metadata.get('source_file', 'Unknown')
                    page = doc.metadata.get('page', 'N/A')
                    st.markdown(f"**{idx+1}. {source_name}** (Page: {page})")
                    st.caption(doc.page_content.replace('\n', ' ')[:300] + "...")
        else:
            st.info("No highly relevant documents found.")
            
        formatted_context = format_docs_with_citations(docs)
        
        system_prompt = """You are an expert, precise AI assistant for answering questions based ONLY on the provided context.
        
        Context Documents:
        {context}
        
        Instructions:
        1. Answer the question using ONLY facts found in the provided context documents.
        2. Do NOT use outside knowledge or hallucinate.
        3. If the context does not contain the answer, reply exactly with: "I could not find relevant information in the provided documents."
        4. Provide inline citations citing the source document using the format: [Doc: filename.pdf, Page: X].
        5. If the user asks for a visual representation, chart, diagram, or process flow, extract the relevant data from the context and generate a Mermaid.js diagram.
        6. When creating a diagram, ALWAYS wrap the code strictly inside a markdown block labeled 'mermaid'. 
        Example:
        ```mermaid
        graph TD;
            A[Start] --> B[Process];
        ```
        """
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "{question}")
        ])
        
        llm = ChatGoogleGenerativeAI(
            model="gemini-3.6-flash", 
            api_key=st.session_state.api_key, 
            temperature=0
        )
        
        chain = prompt | llm | StrOutputParser()
        
        response = st.write_stream(chain.stream({
            "context": formatted_context, 
            "question": query
        }))
        
        # Immediately render any charts that were just generated
        extract_and_render_visuals(response)
        
        st.session_state.messages.append({
            "role": "assistant", 
            "content": response,
            "sources": docs
        })