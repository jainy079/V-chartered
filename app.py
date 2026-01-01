import streamlit as st
import google.generativeai as genai
from PIL import Image

# --- PAGE SETUP ---
st.set_page_config(page_title="CA Final AI Companion", layout="wide")

st.markdown("""
<style>
.big-font { font-size:30px !important; font-weight: bold; color: #1E88E5; }
.ca-header { font-size:20px; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

st.markdown('<p class="big-font">CA Exam & Audit Expert (AI)</p>', unsafe_allow_html=True)
st.write("Specialized for Vanshika's CA Final Preparation")

# --- SIDEBAR (API KEY) ---
with st.sidebar:
    st.header("Settings")
    api_key = st.text_input("Enter Google API Key", type="password")
    st.info("Paste the key starting with 'AIza...' here")
    
    mode = st.radio("Select Mode:", ["📝 Answer Checker (Image)", "🧠 Generate Quiz", "💬 Ask Doubt"])

# --- FUNCTION TO GET GEMINI RESPONSE ---
def get_gemini_response(input_prompt, image=None):
    if not api_key:
        return "Please enter the API Key in the sidebar first."
    
    genai.configure(api_key=api_key)
    # Use Flash model for speed
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    try:
        if image:
            response = model.generate_content([input_prompt, image])
        else:
            response = model.generate_content(input_prompt)
        return response.text
    except Exception as e:
        return f"Error: {str(e)}"

# --- MODE 1: ANSWER CHECKER ---
if mode == "📝 Answer Checker (Image)":
    st.subheader("Upload Handwritten Answer")
    uploaded_file = st.file_uploader("Choose an image...", type=["jpg", "jpeg", "png"])
    
    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.image(image, caption="Uploaded Answer", use_column_width=True)
        
        if st.button("Check as ICAI Examiner"):
            with st.spinner("Analyzing handwriting and logic..."):
                prompt = """
                Act as a strict Examiner for the Institute of Chartered Accountants of India (ICAI). 
                The user has uploaded a handwritten answer for a CA Final/Inter level question.
                
                Your Task:
                1. Identify the topic from the image.
                2. Check the answer strictly based on ICAI Provision, Analysis, and Conclusion format.
                3. Point out specific mistakes (keywords missing, section number errors).
                4. Give it a mark out of 5.
                5. REWRITE the correct answer in the standard ICAI format below.
                """
                response = get_gemini_response(prompt, image)
                st.markdown(response)

# --- MODE 2: QUIZ GENERATOR ---
elif mode == "🧠 Generate Quiz":
    st.subheader("Exam Style Quiz Generator")
    topic = st.text_input("Enter Topic (e.g., Audit of Banks, GST Input Tax Credit)")
    level = st.selectbox("Level", ["CA Inter", "CA Final"])
    
    if st.button("Generate 20 Questions"):
        with st.spinner(f"Creating {level} level questions..."):
            prompt = f"""
            Create a tough mock test of 20 Multiple Choice Questions (MCQs) for {level} students.
            Topic: {topic}.
            The questions should be scenario-based and tricky, similar to recent ICAI exam trends.
            Provide the questions first, and the Answer Key with reasoning at the very end.
            """
            response = get_gemini_response(prompt)
            st.markdown(response)

# --- MODE 3: DOUBT SOLVER ---
elif mode == "💬 Ask Doubt":
    st.subheader("Deep Concept Analysis")
    doubt = st.text_area("Paste your doubt or concept name here:")
    
    if st.button("Explain like a Pro"):
        with st.spinner("Searching deep concepts..."):
            prompt = f"""
            You are a CA Final Topper and Tutor. Explain the following concept: '{doubt}'.
            Explain it in depth. Use examples, relevant Section numbers of Companies Act/Income Tax Act, 
            and relevant Case Laws if applicable. Structure the answer for exam revision.
            """
            response = get_gemini_response(prompt)
            st.markdown(response)
