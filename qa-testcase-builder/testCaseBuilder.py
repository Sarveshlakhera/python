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
class Scenarios(BaseModel):
    scenarios: List[str] = Field(description="A list of distinct test scenarios extracted from the document layer.")

class TestCaseGeneration(BaseModel):
    reasoning: str = Field(description="Step-by-step reasoning deduplicating scenarios and ensuring cross-layer coverage.")
    test_cases: List[Dict[str, Any]] = Field(description="The generated test cases. Keys must strictly match the required columns.")

# --- Helper Functions (Text Extraction) ---
def chunk_text(text: str, chunk_size: int = 15000) -> str:
    """Chunks large text to prevent context window overflow."""
    splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=1000)
    chunks = splitter.split_text(text)
    return chunks[0] if chunks else ""

def process_uploaded_file(uploaded_file) -> str:
    """Routes the uploaded file to the correct extraction method."""
    if not uploaded_file:
        return ""
    
    if uploaded_file.name.endswith('.pdf'):
        try:
            reader = PyPDF2.PdfReader(uploaded_file)
            text = "".join([page.extract_text() + "\n" for page in reader.pages])
            return chunk_text(text)
        except PyPDF2.errors.PdfReadError:
            st.error(f"Could not read {uploaded_file.name}. File might be corrupted.")
            return ""
            
    elif uploaded_file.name.endswith(('.xls', '.xlsx')):
        try:
            dfs = pd.read_excel(uploaded_file, sheet_name=None)
            text = "".join([f"--- Sheet: {sheet_name} ---\n{df.to_csv(index=False)}\n\n" 
                            for sheet_name, df in dfs.items() if not df.empty])
            return chunk_text(text)
        except Exception as e:
            st.error(f"Error extracting Excel text from {uploaded_file.name}: {e}")
            return ""
            
    else: # txt, csv, or code files (.sh, .ksh, .py, etc.)
        try:
            stringio = StringIO(uploaded_file.getvalue().decode("utf-8"))
            return chunk_text(stringio.read())
        except UnicodeDecodeError:
            st.error(f"Encoding error in {uploaded_file.name}. Ensure it is UTF-8 encoded.")
            return ""

def extract_template_headers(template_file, file_name) -> list:
    """Programmatically extracts headers to enforce dynamic schema."""
    try:
        if file_name.endswith('.csv'):
            return pd.read_csv(template_file, nrows=0).columns.tolist()
        elif file_name.endswith(('.xls', '.xlsx')):
            return pd.read_excel(template_file, nrows=0).columns.tolist()
        elif file_name.endswith('.txt'):
            text = process_uploaded_file(template_file)
            return [line.strip() for line in text.split('\n') if line.strip()]
    except Exception as e:
        st.error(f"Error parsing template headers: {e}")
        return []
    return []

# --- AI Core Logic (Layered Synthesis) ---
def extract_layer_scenarios(llm, doc_text: str, layer_name: str, issue_desc: str) -> List[str]:
    """Phase 1: Extracts scenarios strictly for a specific domain layer."""
    
    # Contextual instruction adjustment for Code layer vs Document layers
    if layer_name == "Source Code":
        system_instruction = "You are an expert QA Engineer. Analyze the provided source code snippet and the enhancement request. Extract a detailed list of white-box test scenarios. Focus heavily on hardcoded constraints, conditional logic branches (if/else), exact boundary values, error handling, and expected exceptions."
    else:
        system_instruction = f"You are an expert QA Engineer specializing in the {layer_name} layer. Analyze the provided unstructured documentation and the enhancement request. Extract a detailed list of distinct test scenarios (happy paths, negative paths, boundary cases) strictly relevant to your domain."

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_instruction),
        ("user", """
        <{layer_name}_document>
        {doc_text}
        </{layer_name}_document>
        
        <enhancement_request>
        {issue_desc}
        </enhancement_request>
        """)
    ])
    
    structured_llm = llm.with_structured_output(Scenarios)
    chain = prompt | structured_llm
    result = chain.invoke({"layer_name": layer_name, "doc_text": doc_text, "issue_desc": issue_desc})
    return result.scenarios if result else []

def synthesize_final_tests(llm, aggregated_scenarios: str, required_columns: list, issue_desc: str) -> TestCaseGeneration:
    """Phase 2: Master synthesis to deduplicate and format tests."""
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a Lead QA Automation Engineer. You have been provided with test scenarios extracted from various layers (UI, Backend, Database, Code) for an enhancement request.
        
        REQUIRED TEST CASE COLUMNS:
        {required_columns}
        
        INSTRUCTIONS:
        1. Chain of Thought: Analyze the combined scenarios. Deduplicate overlapping tests. Look for integration gaps between the UI, Backend, Database, and implementation logic.
        2. Test Cases: Generate the final comprehensive test suite. Every single test case object MUST use the EXACT keys listed in the REQUIRED TEST CASE COLUMNS above.
        """),
        ("user", """
        <enhancement_request>
        {issue_desc}
        </enhancement_request>
        
        <extracted_scenarios_from_all_layers>
        {aggregated_scenarios}
        </extracted_scenarios_from_all_layers>
        """)
    ])
    
    structured_llm = llm.with_structured_output(TestCaseGeneration)
    chain = prompt | structured_llm
    return chain.invoke({
        "required_columns": required_columns,
        "aggregated_scenarios": aggregated_scenarios,
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
            st.selectbox("Select Platform", ["Google Gemini", "OpenAI"], key="provider_input")
            st.text_input("API Key", type="password", key="api_key_input", placeholder="Enter the API key for chosen platform")
            st.button("Login", type="primary", use_container_width=True, on_click=login)
        
        st.info("Your API key is used strictly for this session and is not stored permanently.")

def main_app_view():
    """Renders the core application once logged in."""
    col_title, col_logout = st.columns([4, 1])
    with col_title:
        st.title("🧪 Multi-Layer AI Test Generator")
    with col_logout:
        st.write("") 
        st.button("Logout", on_click=logout, use_container_width=True)

    st.markdown("Upload relevant technical documents and code snippets to perform a layered synthesis analysis.")

    # Sidebar for Configuration & Uploads
    with st.sidebar:
        st.success(f"Connected via **{st.session_state['llm_provider']}**")
        st.divider()
        
        st.header("1. Upload Documents & Code")
        st.caption("Upload at least one context file below.")
        ui_file = st.file_uploader("UI/UX Document", type=['pdf', 'txt', 'xls', 'xlsx'])
        backend_file = st.file_uploader("Backend/API Document", type=['pdf', 'txt', 'xls', 'xlsx'])
        db_file = st.file_uploader("Database/Schema Document", type=['pdf', 'txt', 'xls', 'xlsx'])
        general_file = st.file_uploader("General Product Document", type=['pdf', 'txt', 'xls', 'xlsx'])
        
        # --- NEW CODE UPLOADER ---
        code_file = st.file_uploader("Source Code Snippet", type=['py', 'js', 'java', 'cpp', 'cs', 'sh', 'ksh', 'txt', 'json'])
        st.caption("⚠️ **Privacy Warning:** Do not upload sensitive or proprietary source code unless your API key is bound to a zero-data-retention enterprise agreement.")
        
        st.divider()
        st.header("2. Upload Template (Required)")
        template_file = st.file_uploader("Custom Template (Empty with headers)", type=['csv', 'txt', 'xls', 'xlsx'])

    # Main Content Area
    st.header("3. Issue / Enhancement Description")
    issue_description = st.text_area("Describe the bug, feature, or enhancement to test:", height=100)

    if st.button("Generate Tests via Layered Synthesis", type="primary", use_container_width=True):
        if not any([ui_file, backend_file, db_file, general_file, code_file]):
            st.error("Please upload at least one contextual document or code snippet.")
        elif not template_file:
            st.error("Please upload a Test Case Template.")
        elif not issue_description.strip():
            st.error("Please provide an issue or enhancement description.")
        else:
            try:
                # Initialize LLM
                provider = st.session_state['llm_provider']
                api_key = st.session_state['api_key']
                if provider == "OpenAI":
                    llm = ChatOpenAI(model="gpt-4o", temperature=0.1, openai_api_key=api_key)
                else:
                    llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0.1, api_key=api_key)

                # Extract Required Columns
                required_columns = extract_template_headers(template_file, template_file.name)
                if not required_columns:
                    st.error("Failed to extract columns. Please check the template file.")
                    st.stop()

                all_extracted_scenarios = ""
                
                # Execution with Status Container
                with st.status("Running Layered Synthesis Architecture...", expanded=True) as status:
                    # Phase 1 extractions
                    if ui_file:
                        st.write("🔍 Analyzing UI/UX layer...")
                        ui_text = process_uploaded_file(ui_file)
                        ui_scenarios = extract_layer_scenarios(llm, ui_text, "UI/UX", issue_description)
                        all_extracted_scenarios += "\n<UI_SCENARIOS>\n" + "\n".join(ui_scenarios) + "\n</UI_SCENARIOS>\n"

                    if backend_file:
                        st.write("⚙️ Analyzing Backend/API layer...")
                        backend_text = process_uploaded_file(backend_file)
                        backend_scenarios = extract_layer_scenarios(llm, backend_text, "Backend", issue_description)
                        all_extracted_scenarios += "\n<BACKEND_SCENARIOS>\n" + "\n".join(backend_scenarios) + "\n</BACKEND_SCENARIOS>\n"

                    if db_file:
                        st.write("🗄️ Analyzing Database layer...")
                        db_text = process_uploaded_file(db_file)
                        db_scenarios = extract_layer_scenarios(llm, db_text, "Database", issue_description)
                        all_extracted_scenarios += "\n<DATABASE_SCENARIOS>\n" + "\n".join(db_scenarios) + "\n</DATABASE_SCENARIOS>\n"
                        
                    if general_file:
                        st.write("📄 Analyzing General Product layer...")
                        general_text = process_uploaded_file(general_file)
                        general_scenarios = extract_layer_scenarios(llm, general_text, "General", issue_description)
                        all_extracted_scenarios += "\n<GENERAL_SCENARIOS>\n" + "\n".join(general_scenarios) + "\n</GENERAL_SCENARIOS>\n"

                    # --- NEW CODE EXTRACTION ---
                    if code_file:
                        st.write("💻 Analyzing Source Code logic...")
                        code_text = process_uploaded_file(code_file)
                        code_scenarios = extract_layer_scenarios(llm, code_text, "Source Code", issue_description)
                        all_extracted_scenarios += "\n<CODE_SCENARIOS>\n" + "\n".join(code_scenarios) + "\n</CODE_SCENARIOS>\n"

                    # Phase 2 Synthesis
                    st.write("🧠 Lead QA Agent synthesizing final test suite...")
                    result = synthesize_final_tests(llm, all_extracted_scenarios, required_columns, issue_description)
                    
                    status.update(label="Layered Synthesis Complete!", state="complete", expanded=False)

                # Display Results
                with st.expander("🤖 Agent Synthesis Reasoning", expanded=False):
                    st.write(result.reasoning)
                
                if result.test_cases:
                    df = pd.DataFrame(result.test_cases)
                    st.success("Test cases generated successfully!")
                    st.dataframe(df, use_container_width=True)
                    
                    st.write("### Download Test Cases")
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        csv = df.to_csv(index=False).encode('utf-8')
                        st.download_button("📥 Download as CSV", data=csv, file_name='synthesized_tests.csv', mime='text/csv', use_container_width=True)
                        
                    with col2:
                        buffer = BytesIO()
                        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                            df.to_excel(writer, index=False, sheet_name='Tests')
                        excel_data = buffer.getvalue()
                        st.download_button("📥 Download as Excel", data=excel_data, file_name='synthesized_tests.xlsx', mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', use_container_width=True)
                else:
                    st.warning("The AI processed the request but did not return any test cases.")

            except Exception as e:
                st.error(f"An error occurred during synthesis: {e}")

# --- Routing Logic ---
if st.session_state['logged_in']:
    main_app_view()
else:
    login_view()