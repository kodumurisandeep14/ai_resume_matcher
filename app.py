import streamlit as st
import fitz  # PyMuPDF
import docx
from huggingface_hub import InferenceClient
import os
# --- 1. SETUP & TOKEN (SMART SWITCH) ---
HF_TOKEN = None

# Check if we are on Streamlit Cloud (using secrets)

try:
    if "HF_TOKEN" in st.secrets:
        HF_TOKEN = st.secrets["HF_TOKEN"]
except:
    pass  # Ignore errors from secrets

# If secrets don't exist (Local Machine), check for token.txt
if not HF_TOKEN and os.path.exists("token.txt"):
    with open("token.txt", "r") as f:
        HF_TOKEN = f.read().strip()

# Final check
if not HF_TOKEN:
    st.error("API Token not found! Create 'token.txt' locally or add HF_TOKEN to Streamlit Secrets.")
    st.stop()


# Using Llama-3.2-1B-Instruct (ensure you have granted access on Hugging Face)
client = InferenceClient(model="meta-llama/Llama-3.2-1B-Instruct", token=HF_TOKEN)

# --- 2. TEXT EXTRACTION FUNCTION ---
def extract_text(uploaded_file):
    # Get the file extension
    file_extension = uploaded_file.name.split('.')[-1].lower()
    
    if file_extension == 'pdf':
        # PDF Logic: Join text from every page
        doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
        return "".join([page.get_text() for page in doc])
    
    elif file_extension == 'docx':
        # 1. Open the Word doc
        doc = docx.Document(uploaded_file)
        # 2. FIX: Put the list of paragraphs INSIDE the join()
        return "\n".join([para.text for para in doc.paragraphs])
    
    return ""

# --- 3. THE USER INTERFACE (UI) ---
st.set_page_config(st.set_page_config(page_title="Smart Resume Analyzer", page_icon="🧠"))
st.title("🚀 Smart ATS Resume Analyzer")
st.markdown("Compare your resume against any Job Description using Open-Source AI.")
st.markdown( 
    """
    <style>
    .stApp {
        background-color: #0f172a;
        background: linear-gradient(to right, #1e3c72, #2a5298);
        color: white;
    }
      /* "Browse files" button */
    section[data-testid="stFileUploader"] button {
        background-color: #38bdf8;
        color: black;
        font-weight: bold;
        border-radius: 6px;
    }
       /* Fix uploader container */
    section[data-testid="stFileUploader"] {
        background-color: #1e293b;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #334155;
    }

    /* Fix label */
    section[data-testid="stFileUploader"] label {
        color: white !important;
        font-weight: bold;
    }

    /* FORCE visible button */
    section[data-testid="stFileUploader"] button {
        background-color: #38bdf8 !important;
        color: black !important;
        font-weight: bold;
        border-radius: 6px;
        opacity: 1 !important;
        visibility: visible !important;
    }

    /* Remove faded effect */
    section[data-testid="stFileUploader"] button:disabled {
        opacity: 1 !important;
        color: black !important;
    }

    /* Hover effect */
    section[data-testid="stFileUploader"] button:hover {
        background-color: #0ea5e9 !important;
        color: black !important;
    }
     .stButton > button 
     {
        background-color: #1e293b;
        border: 1px solid #334155;
    }
    {
     .stButton > button:hover {
        background-color: #0ea5e9;
        color: black;
    }
    </style>
    """,
    unsafe_allow_html = True
)

col1, col2 = st.columns(2)
with col1:
    uploaded_resume = st.file_uploader("Upload Resume (PDF or DOCX)", type=["pdf", "docx"])
with col2:
    job_desc = st.text_area("Paste Job Description", height=200, placeholder="Paste the full JD here...")

# --- 4. THE AI LOGIC (IMPROVED) ---
if st.button("Analyze My Fit"):
    if uploaded_resume and job_desc:
        with st.spinner("🔍 Senior Recruiter is reviewing your profile..."):
            try:
                resume_text = extract_text(uploaded_resume)
                
                # --- IMPROVED PROMPT ---
                prompt = f"""
                You are a Senior Technical Recruiter and ATS optimization expert.

                Analyze the RESUME against the JOB DESCRIPTION.

                ### Tasks:
                1. Give an ATS Match Score (0–100%)
                2. Identify missing keywords and skills
                3. Suggest improvements (bullet points)
                4.Generate 3 highly optimized ATS bullet points using this formula:
                - Start with a strong action verb
                - Include measurable impact (numbers, %, results)
                - Include keywords from the job description
                - Keep each bullet under 25 words

                Use this format:
                • Action Verb + Task + Tools/Skills + Measurable Result

                Example:
                • Increased API performance by 35% using Python and Redis caching, improving system response time for 10k+ users
                5. Final verdict: Should this candidate be interviewed?

                ### Output Format:

                **ATS Score:**  
                **Missing Skills:**  
                **Suggested Improvements:** 
                **which project they can improve** 
                **Optimized Bullet Points:**  
                **Final Verdict:**  

                ---

                RESUME:
                {resume_text}

                ---

                JOB DESCRIPTION:
                {job_desc}
                """
                
                messages = [{"role": "user", "content": prompt}]
                
                response = client.chat_completion(
                    messages=messages,
                    max_tokens=800,  # Increased to allow for more detailed feedback
                    temperature=0
                )
                
                # Handling response format
                if isinstance(response, list):
                    result_text = response[0].generated_text
                else:
                    result_text = response.choices[0].message.content
                
                st.success("Analysis Complete!")
                st.markdown("---")
                st.markdown(result_text)
                
                # OPTIONAL: Add a download button for the feedback
                st.download_button("Download Feedback Report", result_text, file_name="AI_Resume_Critique.txt")
                
            except Exception as e:
                st.error(f"Error: {e}")
    else:
        st.warning("Please upload a resume and paste a job description first.")

