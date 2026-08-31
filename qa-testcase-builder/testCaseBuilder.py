import streamlit as st
import pandas as pd
import PyPDF2
import json
import os
from io import StringIO
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# LLM Providers
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI

# --- Page Configuration ---
st.set_page_config(page_title="AI QA Test Case Generator", page_icon="🧪", layout="wide")

# --- Helper Functions ---
def extract_text_from_pdf(pdf_file):
    """Extracts text from an uploaded PDF file."""
    reader = PyPDF2.PdfReader(pdf_file)
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n"
    return text

def extract_text_from_txt(txt_file):
    """Extracts text from an uploaded TXT file."""
    stringio = StringIO(txt_file.getvalue().decode("utf-8"))
    return stringio.read()

def parse_template(template_file, file_name):
    """Extracts headers or sample structure from a template file."""
    if file_name.endswith('.csv'):
        df = pd.read_csv(template_file, nrows=5) 
        return f"CSV Headers: {', '.join(df.columns.tolist())}\nSample Data:\n{df.to_csv(index=False)}"
    elif file_name.endswith('.txt'):
        return extract_text_from_txt(template_file)
    return ""

# --- LangChain Orchestration ---
def generate_test_cases(llm, doc_text, template_structure, issue_desc):
    """Handles the orchestration regardless of which LLM provider was passed in."""
    
    # STEP A: Analyze the template and generate format instructions
    template_prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a data formatting expert. Analyze the provided test case template structure. "
                   "Output a strict list of the required JSON keys (columns) that the user expects in their test cases. "
                   "Do not include any other text."),
        ("user", "Template Structure:\n{template_structure}")
    ])
    
    chain_a = template_prompt | llm | StrOutputParser()
    required_columns = chain_a.invoke({"template_structure": template_structure})
    
    # STEP B: Generate the test cases using the extracted format
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
    raw_json_output = chain_b.invoke({
        "required_columns": required_columns,
        "doc_text": doc_text,
        "issue_desc": issue_desc
    })
    
    return raw_json_output

# --- Streamlit UI ---
st.title("🧪 AI QA Test Case Generator")
st.markdown("Upload your product documentation and your team's test case template to dynamically generate structured QA tests.")

# Sidebar for Configuration & Uploads
with st.sidebar:
    st.header("Configuration")
    
    # Provider Selection
    llm_provider = st.selectbox("Select AI Provider", ["Google Gemini", "OpenAI"])
    
    # Dynamic API Key Input
    if llm_provider == "OpenAI":
        api_key = st.text_input("OpenAI API Key (sk-...)", type="password")
        model_name = "gpt-4o"
    elif llm_provider == "Google Gemini":
        api_key = st.text_input("Google Gemini API Key", type="password")
        model_name = "gemini-1.5-pro"
        
    st.divider()
    
    st.header("1. Upload Documents")
    doc_file = st.file_uploader("Upload Product Document (PDF/TXT)", type=['pdf', 'txt'])
    
    st.header("2. Upload Template")
    template_file = st.file_uploader("Upload Custom Template (CSV/TXT)", type=['csv', 'txt'])

# Main Content Area
st.header("3. Issue / Enhancement Description")
issue_description = st.text_area("Describe the bug, feature, or enhancement to test:", height=150, 
                                 placeholder="e.g., The user login endpoint should now lock the account after 5 failed attempts...")

# Action Button
if st.button("Generate Tests", type="primary", use_container_width=True):
    if not api_key:
        st.error(f"Please provide your {llm_provider} API Key in the sidebar.")
    elif not doc_file:
        st.error("Please upload a Product Document.")
    elif not template_file:
        st.error("Please upload a Test Case Template.")
    elif not issue_description.strip():
        st.error("Please provide an issue or enhancement description.")
    else:
        with st.spinner(f"Generating tests using {llm_provider}..."):
            try:
                # Initialize the chosen LLM
                if llm_provider == "OpenAI":
                    llm = ChatOpenAI(model=model_name, temperature=0.2, openai_api_key=api_key)
                elif llm_provider == "Google Gemini":
                    # Initialize Gemini API
                    llm = ChatGoogleGenerativeAI(model=model_name, temperature=0.2, api_key=api_key)
                
                # 1. Parse Document
                if doc_file.name.endswith('.pdf'):
                    doc_text = extract_text_from_pdf(doc_file)
                else:
                    doc_text = extract_text_from_txt(doc_file)
                
                # 2. Parse Template
                template_structure = parse_template(template_file, template_file.name)
                
                # 3. Orchestrate LangChain processing (pass the initialized LLM)
                json_result = generate_test_cases(llm, doc_text, template_structure, issue_description)
                
                # 4. Convert JSON to Pandas DataFrame
                try:
                    # Clean up the output in case the LLM added markdown formatting
                    clean_json = json_result.replace("```json", "").replace("```", "").strip()
                    test_cases_list = json.loads(clean_json)
                    df = pd.DataFrame(test_cases_list)
                    
                    st.success("Test cases generated successfully!")
                    
                    # Display the DataFrame
                    st.dataframe(df, use_container_width=True)
                    
                    # Provide Download Button
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
                st.error(f"An error occurred: {e}")