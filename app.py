## Import modules and libraries
from dotenv import load_dotenv
load_dotenv()
import streamlit as st
import io
import base64
import os
from PIL import Image
import pdf2image
from pdf2image.exceptions import PDFInfoNotInstalledError
import google.generativeai as genai 
from openai import OpenAI



## configure the API client
_openai_client = OpenAI(api_key = os.getenv("openai_API_KEY"))
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))  

## get OpenAI response
def get_openai_response(job_description, Resume, prompt):
    base64_image = Resume[0]["data"]
    user_content = [
        {"type": "text", "text": job_description},
        {"type": "text", "text": prompt},
        {
            "type": "image_url",
            "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"},
        },
    ]
    response = _openai_client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0.2,
        messages=[{"role": "user", "content": user_content}],
    )
    return response.choices[0].message.content

## get gemini response
def get_gemini_response(job_description, Resume, prompt):
     model = genai.GenerativeModel("gemini-2.5-pro")
     response = model.generate_content([job_description, Resume[0], prompt])
     return response.text

## uploading the resume
def input_Resume_pdf(uploaded_file, poppler_path=None):
    if uploaded_file is not None:
        ##convert pdf to image
        if poppler_path:
            images = pdf2image.convert_from_bytes(uploaded_file.read(), poppler_path=poppler_path)
        else:
            images = pdf2image.convert_from_bytes(uploaded_file.read())

        first_page = images[0]

        # Convert to bytes
        img_byte_arr = io.BytesIO()
        first_page.save(img_byte_arr, format='JPEG')
        img_byte_arr = img_byte_arr.getvalue()

        pdf_parts = [
        {
            "mime_type": "image/jpeg",
            "data": base64.b64encode(img_byte_arr).decode()  # encode to base64
        }
        ]
        return pdf_parts
    else:
        raise FileNotFoundError("No file uploaded")

 ##Streamlite app

st.set_page_config(page_title="ATS Resume Matching")
st.header("ATS Tracking System")
input_text = st.text_area("Job Description:", key="input")
uploaded_file = st.file_uploader("Upload your resume (PDF)...")
providers = st.sidebar.multiselect("Model providers", ["OpenAI", "Gemini"], default=["OpenAI", "Gemini"])

# Optional: allow user to provide Poppler path if not on PATH
default_poppler = os.getenv("POPPLER_PATH", "")
poppler_path_input = st.sidebar.text_input(
    "Poppler bin path (optional)",
    value=default_poppler,
    help="Examples: C:/Program Files/poppler-24.08.0/Library/bin or C:/Program Files/poppler-24.08.0/bin",
)

def _normalize_poppler_path(path_str: str):
    if not path_str:
        return "", []
    raw = path_str.strip().strip('"')
    normalized = os.path.expanduser(os.path.expandvars(raw))
    # If a file is provided, use its directory
    candidate_dir = os.path.dirname(normalized) if os.path.isfile(normalized) else normalized
    required_bins = ["pdfinfo.exe", "pdftoppm.exe"]
    missing = [exe for exe in required_bins if not os.path.exists(os.path.join(candidate_dir, exe))]
    return candidate_dir, missing

poppler_path, poppler_missing = _normalize_poppler_path(poppler_path_input)
if poppler_path_input:
    if poppler_missing:
        st.sidebar.error(
            "Poppler binaries not found in the provided folder. Missing: "
            + ", ".join(poppler_missing)
            + "\nCheck that the folder contains pdfinfo.exe and pdftoppm.exe."
        )
    else:
        st.sidebar.success("Poppler detected: " + poppler_path)
  
if uploaded_file is not None:
    st.write("PDF uploaded succesfully")

submit1 = st.button("Tell me about the resume")
# submit2 = st.button("How can i improvise my skills")
submit3 = st.button("Percentage match")

input_prompt1 = '''
 You are an experienced HR with Tech experiencein the field of data science, full stack
 web development, BigData Engineering, DEVOPS, Data Analyst.
Your task is to review the provided resume aganist the job description for these profiles.
  Please share your professional evaluation on whether the candidates profile aligns withthe role
  Highlight strengths and weaknesses of the applicant in relation to the specified job requirements.
'''

input_prompt_3 = '''
You are a skilled ATS(Applicant Tracking System) scanner with a deep understanding of Datascience,full stack
 web development, BigData Engineering, DEVOPS, Data Analyst and deep ATS functionality
 Your role is to evaluate the resume aganist the provided job description give the percentage match if the resume 
 matches the job description. First the output should come as a percentage and then keywords missing as final thoughts. 


'''
if submit1:
    if uploaded_file is not None:
        try:
            if poppler_path_input and poppler_missing:
                st.error("The Poppler folder you entered is missing required files: " + ", ".join(poppler_missing))
                st.info("Use a folder like C:/Program Files/poppler-<version>/Library/bin or .../bin that contains pdfinfo.exe and pdftoppm.exe.")
                st.stop()
            pdf_content = input_Resume_pdf(uploaded_file, poppler_path=poppler_path or None)
        except PDFInfoNotInstalledError:
            st.error("Poppler (pdfinfo) not found. Add Poppler's bin folder to PATH or enter it in the sidebar. Typical paths: C:/Program Files/poppler-<version>/Library/bin or C:/Program Files/poppler-<version>/bin")
            st.stop()
        responses = []
        if "OpenAI" in providers:
            try:
                responses.append(("OpenAI", get_openai_response(input_prompt1,pdf_content,input_text)))
            except Exception as e:
                responses.append(("OpenAI", f"Error: {e}"))
        if "Gemini" in providers:
            try:
                responses.append(("Gemini", get_gemini_response(input_prompt1,pdf_content,input_text)))
            except Exception as e:
                responses.append(("Gemini", f"Error: {e}"))
        for provider_name, resp in responses:
            st.subheader(f"Response - {provider_name}")
            st.write(resp)
    else:
        st.write("Please upload the Resume")
elif submit3:
    if uploaded_file is not None:
        try:
            if poppler_path_input and poppler_missing:
                st.error("The Poppler folder you entered is missing required files: " + ", ".join(poppler_missing))
                st.info("Use a folder like C:/Program Files/poppler-<version>/Library/bin or .../bin that contains pdfinfo.exe and pdftoppm.exe.")
                st.stop()
            pdf_content = input_Resume_pdf(uploaded_file, poppler_path=poppler_path or None)
        except PDFInfoNotInstalledError:
            st.error("Poppler (pdfinfo) not found. Add Poppler's bin folder to PATH or enter it in the sidebar. Typical paths: C:/Program Files/poppler-<version>/Library/bin or C:/Program Files/poppler-<version>/bin")
            st.stop()
        responses = []
        if "OpenAI" in providers:
            try:
                responses.append(("OpenAI", get_openai_response(input_prompt_3,pdf_content,input_text)))
            except Exception as e:
                responses.append(("OpenAI", f"Error: {e}"))
        if "Gemini" in providers:
            try:
                responses.append(("Gemini", get_gemini_response(input_prompt_3,pdf_content,input_text)))
            except Exception as e:
                responses.append(("Gemini", f"Error: {e}"))
        for provider_name, resp in responses:
            st.subheader(f"Response - {provider_name}")
            st.write(resp)
    else:
        st.write("Please upload the Resume")

    
