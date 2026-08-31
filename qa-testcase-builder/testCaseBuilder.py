import streamlit as st
import pandas as pd
import PyPDF2
import json
from io import StringIO
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI

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
    
# --- Helper Functions (Updated for Full Excel Support) ---
def extract_text_from_pdf(pdf_file):
    reader = PyPDF2.PdfReader(pdf_file)
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n"
    return text

def extract_text_from_txt(txt_file):
    stringio = StringIO(txt_file.getvalue().decode("utf-8"))
    return stringio.read()

def extract_text_from_excel(excel_file):
    """Extracts text from all sheets of an Excel Product Document."""
    try:
        # Read all sheets into a dictionary of dataframes
        dfs = pd.read_excel(excel_file, sheet_name=None)
        text = ""
        for sheet_name, df in dfs.items():
            text += f"--- Sheet: {sheet_name} ---\n"
            # Convert to CSV format string (compact and LLM-friendly)
            text += df.to_csv(index=False) + "\n\n"
        return text
    except Exception as e:
        return f"Error extracting text from Excel document: {e}"

def parse_template(template_file, file_name):
    """Extracts headers or sample structure from CSV, TXT, or Excel."""
    try:
        if file_name.endswith('.csv'):
            df = pd.read_csv(template_file, nrows=5) 
            return f"Columns: {', '.join(df.columns.tolist())}\nSample Data:\n{df.to_csv(index=False)}"
        
        elif file_name.endswith(('.xls', '.xlsx')):
            df = pd.read_excel(template_file, nrows=5) 
            return f"Columns: {', '.join(df.columns.tolist())}\nSample Data:\n{df.to_csv(index=False)}"
        
        elif file_name.endswith('.txt'):
            return extract_text_from_txt(template_file)
            
    except Exception as e:
        return f"Error parsing template: {e}"
    
    return ""

def generate_test_cases(llm, doc_text, template_structure, issue_desc):
    template_prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a data formatting expert. Analyze the provided test case template structure. "
                   "Output a strict list of the required JSON keys (columns) that the user expects in their test cases. "
                   "Do not include any other text."),
        ("user", "Template Structure:\n{template_structure}")
    ])
    
    chain_a = template_prompt | llm | StrOutputParser()
    required_columns = chain_a.invoke({"template_structure": template_structure})
    
    generation_prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a Senior QA Automation Engineer. Generate comprehensive test cases based on the provided product document and enhancement description.
        
        CRITICAL INSTRUCTION - OUTPUT FORMAT:
        You MUST output ONLY a valid JSON array of objects. 
        Each object in the array must represent a single test case.
        Each object MUST use EXACTLY these keys based on the user's template: {required_columns}
        
        Do not include markdown formatting (like ```json). Just the raw JSON array.
        Cover Happy Paths, Negative Paths, Boundary Cases, and Regression Risks."""),
        ("user", "Product Context:\n{doc_text}\n\nRequested Enhancement/Issue:\n{issue_desc}")
    ])
    
    chain_b = generation_prompt | llm | StrOutputParser()
    return chain_b.invoke({
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
        # Updated to accept xls and xlsx
        doc_file = st.file_uploader("Upload Product Document", type=['pdf', 'txt', 'xls', 'xlsx'])
        
        st.header("2. Upload Template")
        template_file = st.file_uploader("Upload Custom Template", type=['csv', 'txt', 'xls', 'xlsx'])

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
                        llm = ChatGoogleGenerativeAI(model="gemini-1.5-pro", temperature=0.2, api_key=api_key)
                    
                    # Extract document text based on file type (Now includes Excel routing)
                    if doc_file.name.endswith('.pdf'):
                        doc_text = extract_text_from_pdf(doc_file)
                    elif doc_file.name.endswith(('.xls', '.xlsx')):
                        doc_text = extract_text_from_excel(doc_file)
                    else:
                        doc_text = extract_text_from_txt(doc_file)
                    
                    # Parse the template 
                    template_structure = parse_template(template_file, template_file.name)
                    
                    # Send to LangChain
                    json_result = generate_test_cases(llm, doc_text, template_structure, issue_description)
                    
                    try:
                        clean_json = json_result.replace("```json", "").replace("```", "").strip()
                        test_cases_list = json.loads(clean_json)
                        df = pd.DataFrame(test_cases_list)
                        
                        st.success("Test cases generated successfully!")
                        st.dataframe(df, use_container_width=True)
                        
                        csv = df.to_csv(index=False).encode('utf-8')
                        st.download_button(
                            label="Download Test Cases as CSV",
                            data=csv,
                            file_name='generated_test_cases.csv',
                            mime='text/csv',
                        )
                    except json.JSONDecodeError:
                        st.error("The AI failed to generate valid JSON. Raw output below:")
                        st.write(json_result)
                        
                except Exception as e:
                    st.error(f"An error occurred. Please check your API key and try again. Error details: {e}")

# --- Routing Logic ---
if st.session_state['logged_in']:
    main_app_view()
else:
    login_view()