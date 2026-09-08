import streamlit as st
import pandas as pd
import PyPDF2
from io import StringIO, BytesIO
from typing import List, Dict, Any
from pydantic import BaseModel, Field

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_text_splitters import RecursiveCharacterTextSplitter

# --- Page Configuration ---
st.set_page_config(page_title="AI QA Test Case Generator", page_icon="🧪", layout="wide")

# --- Session State Management ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'api_key' not in st.session_state:
    st.session_state['api_key'] = ''
if 'llm_provider' not in st.session_state:
    st.session_state['llm_provider'] = ''

def login():
    """Handles the authentication logic using the API Key."""
    provider = st.session_state['provider_input']
    key = st.session_state['api_key_input'].strip()
    
    if key:
        st.session_state['logged_in'] = True
        st.session_state['llm_provider'] = provider
        st.session_state['api_key'] = key
    else:
        st.error(f"Please enter a valid {provider} API Key to continue.")

def logout():
    """Clears the session state and logs the user out."""
    st.session_state['logged_in'] = False
    st.session_state['api_key'] = ''
    st.session_state['llm_provider'] = ''
    
# --- Pydantic Data Models ---
class TestCaseGeneration(BaseModel):
    reasoning: str = Field(description="Step-by-step reasoning identifying affected modules, happy paths, negative paths, and boundary conditions.")
    test_cases: List[Dict[str, Any]] = Field(description="The generated test cases. Keys must strictly match the required columns.")

# --- Helper Functions ---
def chunk_text(text: str, chunk_size: int = 15000) -> str:
    """Chunks large text to prevent context window overflow."""
    splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=1000)
    chunks = splitter.split_text(text)
    if len(chunks) > 1:
        st.warning("Document is very large. Only processing the most relevant sections to maintain precision.")
    return chunks[0] if chunks else ""

def extract_text_from_pdf(pdf_file) -> str:
    try:
        reader = PyPDF2.PdfReader(pdf_file)
        text = "".join([page.extract_text() + "\n" for page in reader.pages])
        return chunk_text(text)
    except PyPDF2.errors.PdfReadError:
        st.error("Could not read the PDF. The file might be corrupted or encrypted.")
        return ""

def extract_text_from_txt(txt_file) -> str:
    try:
        stringio = StringIO(txt_file.getvalue().decode("utf-8"))
        return chunk_text(stringio.read())
    except UnicodeDecodeError:
        st.error("Encoding error. Please ensure the text file is UTF-8 encoded.")
        return ""

def extract_text_from_excel(excel_file) -> str:
    try:
        dfs = pd.read_excel(excel_file, sheet_name=None)
        text = ""
        for sheet_name, df in dfs.items():
            if not df.empty:
                text += f"--- Sheet: {sheet_name} ---\n{df.to_csv(index=False)}\n\n"
        return chunk_text(text)
    except pd.errors.EmptyDataError:
        st.error("The uploaded Excel file appears to be empty.")
        return ""
    except Exception as e:
        st.error(f"Error extracting Excel text: {e}")
        return ""

def extract_template_headers(template_file, file_name) -> list:
    """Programmatically extracts headers to enforce dynamic schema."""
    try:
        if file_name.endswith('.csv'):
            df = pd.read_csv(template_file, nrows=0) 
            return df.columns.tolist()
        elif file_name.endswith(('.xls', '.xlsx')):
            df = pd.read_excel(template_file, nrows=0) 
            return df.columns.tolist()
        elif file_name.endswith('.txt'):
            text = extract_text_from_txt(template_file)
            return [line.strip() for line in text.split('\n') if line.strip()]
    except Exception as e:
        st.error(f"Error parsing template headers: {e}")
        return []
    return []

def generate_test_cases(llm, doc_text, required_columns, issue_desc) -> TestCaseGeneration:
    """Generates structured test cases using LangChain and Pydantic."""
    
    generation_prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an elite Senior QA Automation Engineer. Your task is to generate comprehensive test cases based on the provided product document and enhancement request.
        
        REQUIRED TEST CASE COLUMNS:
        {required_columns}
        
        INSTRUCTIONS:
        1. Chain of Thought: First, analyze the enhancement request against the product document. Identify affected modules, happy paths, negative paths, boundary cases, and regression risks.
        2. Test Cases: Generate the test cases. Every single test case object MUST use the EXACT keys listed in the REQUIRED TEST CASE COLUMNS above.
        
        EXAMPLE OF EXCELLENT QA DEPTH:
        - Do not just test "User can login". Test "User account is locked after 5 consecutive failed attempts with incorrect password within a 10-minute window."
        """),
        ("user", """
        <product_document>
        {doc_text}
        </product_document>
        
        <enhancement_request>
        {issue_desc}
        </enhancement_request>
        """)
    ])
    
    # Enforce Pydantic schema structure natively 
    structured_llm = llm.with_structured_output(TestCaseGeneration)
    chain = generation_prompt | structured_llm
    
    return chain.invoke({
        "required_columns": required_columns,
        "doc_text": doc_text,
        "issue_desc": issue_desc
    })

# --- UI Views ---

def login_view():
    """Renders the gateway login screen asking for API keys."""
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col2:
        st.write("") 
        st.write("")
        st.markdown("<h2 style='text-align: center; color: #1E88E5;'>Sign In</h2>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center;'>Authenticate with your AI Provider</p>", unsafe_allow_html=True)
        
        with st.container(border=True):
            st.selectbox("Select AI Provider", ["Google Gemini", "OpenAI"], key="provider_input")
            st.text_input("API Key", type="password", key="api_key_input", placeholder="Enter your API key")
            st.button("Login", type="primary", use_container_width=True, on_click=login)
        
        st.info("Your API key is used strictly for this session and is not stored permanently.")

def main_app_view():
    """Renders the core application once logged in."""
    col_title, col_logout = st.columns([4, 1])
    with col_title:
        st.title("🧪 AI QA Test Case Generator")
    with col_logout:
        st.write("") 
        st.button("Logout", on_click=logout, use_container_width=True)

    st.markdown("Upload your product documentation and your team's test case template to dynamically generate structured QA tests.")

    # Sidebar for Configuration & Uploads
    with st.sidebar:
        st.success(f"Connected via **{st.session_state['llm_provider']}**")
        st.divider()
        
        st.header("1. Upload Documents")
        doc_file = st.file_uploader("Upload Product Document", type=['pdf', 'txt', 'xls', 'xlsx'])
        
        st.header("2. Upload Template")
        template_file = st.file_uploader("Upload Custom Template (Empty with headers)", type=['csv', 'txt', 'xls', 'xlsx'])

    # Main Content Area
    st.header("3. Issue / Enhancement Description")
    issue_description = st.text_area("Describe the bug, feature, or enhancement to test:", height=150, 
                                     placeholder="e.g., The user login endpoint should now lock the account after 5 failed attempts...")

    if st.button("Generate Tests", type="primary", use_container_width=True):
        if not doc_file:
            st.error("Please upload a Product Document.")
        elif not template_file:
            st.error("Please upload a Test Case Template.")
        elif not issue_description.strip():
            st.error("Please provide an issue or enhancement description.")
        else:
            with st.spinner(f"Generating tests using {st.session_state['llm_provider']}..."):
                try:
                    provider = st.session_state['llm_provider']
                    api_key = st.session_state['api_key']
                    
                    if provider == "OpenAI":
                        llm = ChatOpenAI(model="gpt-4o", temperature=0.2, openai_api_key=api_key)
                    elif provider == "Google Gemini":
                        llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0.2, api_key=api_key)
                    
                    # Extract document text
                    if doc_file.name.endswith('.pdf'):
                        doc_text = extract_text_from_pdf(doc_file)
                    elif doc_file.name.endswith(('.xls', '.xlsx')):
                        doc_text = extract_text_from_excel(doc_file)
                    else:
                        doc_text = extract_text_from_txt(doc_file)
                    
                    # Programmatically extract required headers
                    required_columns = extract_template_headers(template_file, template_file.name)
                    
                    if not required_columns:
                        st.error("Failed to extract columns from the template. Please check the file format.")
                        st.stop()
                    
                    # Send to LangChain with Pydantic structured output
                    result: TestCaseGeneration = generate_test_cases(llm, doc_text, required_columns, issue_description)
                    
                    # Display Reasoning
                    with st.expander("🤖 AI Test Strategy & Reasoning", expanded=False):
                        st.write(result.reasoning)
                    
                    # Display Dataframe and Download Buttons
                    if result.test_cases:
                        df = pd.DataFrame(result.test_cases)
                        st.success("Test cases generated successfully!")
                        st.dataframe(df, use_container_width=True)
                        
                        st.write("### Download Test Cases")
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            csv = df.to_csv(index=False).encode('utf-8')
                            st.download_button(
                                label="📥 Download as CSV",
                                data=csv,
                                file_name='generated_test_cases.csv',
                                mime='text/csv',
                                use_container_width=True
                            )
                            
                        with col2:
                            buffer = BytesIO()
                            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                                df.to_excel(writer, index=False, sheet_name='Test Cases')
                            excel_data = buffer.getvalue()
                            
                            st.download_button(
                                label="📥 Download as Excel",
                                data=excel_data,
                                file_name='generated_test_cases.xlsx',
                                mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                                use_container_width=True
                            )
                    else:
                        st.warning("The AI processed the request but did not return any test cases.")
                        
                except Exception as e:
                    st.error(f"An error occurred. Please check your API key and try again. Error details: {e}")

# --- Routing Logic ---
if st.session_state['logged_in']:
    main_app_view()
else:
    login_view()