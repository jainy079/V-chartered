import streamlit as st
import google.generativeai as genai
from PIL import Image
import time
import sqlite3
import hashlib

# ==========================================
# 👇 CONFIGURATION 👇
# ==========================================
GOOGLE_API_KEY = "AIzaSyCwjIu4Hc4HczJUeZdfVgw1j1VxWPZq-JM"  # Apni Key Check karlena
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash')

st.set_page_config(
    page_title="V-Chartered",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ==========================================
# 🎨 CUSTOM CSS (Startup Look & Mobile Friendly)
# ==========================================
st.markdown("""
<style>
    /* Mobile Friendly Fonts */
    html, body, [class*="css"] {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    
    /* Card Styling */
    .feature-card {
        background-color: white;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.08);
        text-align: center;
        border: 1px solid #e0e0e0;
        margin-bottom: 20px;
        transition: transform 0.2s;
    }
    .feature-card:hover {
        transform: scale(1.02);
        border-color: #004B87;
    }
    
    /* Splash Screen Text */
    .credits {
        font-size: 14px;
        color: #666;
        margin-top: 10px;
        font-style: italic;
    }

    /* ICAI Blue Theme Buttons */
    .stButton>button {
        background-color: #004B87;
        color: white;
        border-radius: 8px;
        width: 100%;
        font-weight: 600;
    }
    
    /* Kuchu Box */
    .kuchu-msg {
        background-color: #E3F2FD;
        border-left: 5px solid #2196F3;
        padding: 15px;
        border-radius: 5px;
        margin-top: 10px;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 💾 DATABASE HANDLING (Sign Up/Login)
# ==========================================
def init_db():
    conn = sqlite3.connect('vchartered_users.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (email TEXT PRIMARY KEY, username TEXT, password TEXT)''')
    conn.commit()
    conn.close()

def create_user(email, username, password):
    conn = sqlite3.connect('vchartered_users.db')
    c = conn.cursor()
    hashed_pw = hashlib.sha256(password.encode()).hexdigest()
    try:
        c.execute("INSERT INTO users VALUES (?, ?, ?)", (email, username, hashed_pw))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def check_login(email, password):
    conn = sqlite3.connect('vchartered_users.db')
    c = conn.cursor()
    hashed_pw = hashlib.sha256(password.encode()).hexdigest()
    c.execute("SELECT username FROM users WHERE email=? AND password=?", (email, hashed_pw))
    result = c.fetchone()
    conn.close()
    return result[0] if result else None

# Initialize DB on load
init_db()

# ==========================================
# 🌊 STATE MANAGEMENT
# ==========================================
if 'logged_in' not in st.session_state: st.session_state['logged_in'] = False
if 'user_name' not in st.session_state: st.session_state['user_name'] = ""
if 'current_page' not in st.session_state: st.session_state['current_page'] = "Login"
if 'generated_questions' not in st.session_state: st.session_state['generated_questions'] = None

# ==========================================
# 1️⃣ SPLASH SCREEN
# ==========================================
if 'splash_shown' not in st.session_state:
    placeholder = st.empty()
    with placeholder.container():
        st.markdown("<br><br><br>", unsafe_allow_html=True)
        st.markdown("<h1 style='text-align: center; color: #004B87; font-size: 60px;'>V-Chartered</h1>", unsafe_allow_html=True)
        st.markdown("<h3 style='text-align: center; color: #333;'>Redefining CA Preparation</h3>", unsafe_allow_html=True)
        
        # CREDITS (Tera Naam)
        st.markdown("<p style='text-align: center;' class='credits'>Made by <b>Atishay Jain</b> & <b>Google Gemini Services</b></p>", unsafe_allow_html=True)
        
        bar = st.progress(0)
        for i in range(100):
            time.sleep(0.015)
            bar.progress(i + 1)
        time.sleep(1)
    placeholder.empty()
    st.session_state['splash_shown'] = True

# ==========================================
# 2️⃣ AUTHENTICATION (Login / Sign Up)
# ==========================================
if not st.session_state['logged_in']:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("### Welcome to V-Chartered 🎓")
        auth_mode = st.radio("Choose Option:", ["Login", "Sign Up"], horizontal=True)
        
        if auth_mode == "Sign Up":
            with st.form("signup_form"):
                new_email = st.text_input("Email ID (Gmail)")
                new_user = st.text_input("Full Name")
                new_pass = st.text_input("Create Password", type="password")
                if st.form_submit_button("Register"):
                    if new_email and new_user and new_pass:
                        if create_user(new_email, new_user, new_pass):
                            st.success("Account Created! Please Login.")
                        else:
                            st.error("Email already exists!")
                    else:
                        st.warning("All fields are required.")
                        
        else: # Login
            with st.form("login_form"):
                email = st.text_input("Email ID")
                password = st.text_input("Password", type="password")
                if st.form_submit_button("Login Securely"):
                    user = check_login(email, password)
                    if user:
                        st.session_state['logged_in'] = True
                        st.session_state['user_name'] = user
                        st.session_state['current_page'] = "Home"
                        st.rerun()
                    else:
                        st.error("Invalid Email or Password.")
    st.stop()

# ==========================================
# 3️⃣ NAVIGATION HANDLER
# ==========================================
def go_home(): st.session_state['current_page'] = "Home"

# Sidebar for Logout only
with st.sidebar:
    st.write(f"👤 **{st.session_state['user_name']}**")
    if st.button("Logout"):
        st.session_state['logged_in'] = False
        st.rerun()
    if st.session_state['current_page'] != "Home":
        if st.button("🏠 Back to Home"):
            go_home()
            st.rerun()

# ==========================================
# 4️⃣ HOME PAGE (ICONS DASHBOARD)
# ==========================================
if st.session_state['current_page'] == "Home":
    st.title(f"Hello, {st.session_state['user_name'].split()[0]} 👋")
    st.write("What would you like to do today?")
    st.markdown("---")
    
    c1, c2 = st.columns(2)
    c3, c4 = st.columns(2)
    
    with c1:
        st.markdown('<div class="feature-card"><h3>📑 Mock Test Series</h3><p>10 Questions Set (Inter/Final)</p></div>', unsafe_allow_html=True)
        if st.button("Start Mock Test"):
            st.session_state['current_page'] = "MockTest"
            st.rerun()
            
    with c2:
        st.markdown('<div class="feature-card"><h3>📸 External Checker</h3><p>Upload any Q & A Photo</p></div>', unsafe_allow_html=True)
        if st.button("Open Answer Scanner"):
            st.session_state['current_page'] = "ExternalCheck"
            st.rerun()
            
    with c3:
        st.markdown('<div class="feature-card"><h3>🤖 Ask Kuchu</h3><p>Doubts + Motivation</p></div>', unsafe_allow_html=True)
        if st.button("Talk to Kuchu"):
            st.session_state['current_page'] = "Kuchu"
            st.rerun()

    with c4:
        st.markdown('<div class="feature-card"><h3>📚 Study Material</h3><p>Subject-wise Notes (Coming Soon)</p></div>', unsafe_allow_html=True)
        st.button("Access Library") # Placeholder

# ==========================================
# 5️⃣ FEATURE: MOCK TEST (10 Q SET)
# ==========================================
elif st.session_state['current_page'] == "MockTest":
    st.title("📑 CA Exam Simulator")
    
    # Selection Phase
    if st.session_state['generated_questions'] is None:
        col1, col2 = st.columns(2)
        with col1:
            level = st.selectbox("Select Level", ["CA Foundation", "CA Inter", "CA Final"])
        with col2:
            subject = st.text_input("Enter Subject (e.g., Audit, Law)")
            
        if st.button("Generate 10 Questions Set"):
            with st.spinner("Preparing Question Paper..."):
                prompt = f"""
                Create a QUESTION PAPER of 10 Tough Questions for {level} - {subject}.
                Mix of Case Studies and Descriptive.
                Format:
                Q1. [Question] (Marks: 5)
                ...
                Q10. [Question] (Marks: 5)
                Do NOT include answers.
                """
                response = model.generate_content(prompt)
                st.session_state['generated_questions'] = response.text
                st.rerun()
                
    # Exam Phase
    else:
        st.markdown("### 📝 Question Paper")
        with st.expander("Click to View Questions", expanded=True):
            st.markdown(st.session_state['generated_questions'])
        
        st.markdown("---")
        st.markdown("### 📤 Submit Answer Sheet")
        st.info("Write answers on paper, click photos, and upload here. You can submit early.")
        
        uploaded_files = st.file_uploader("Upload Answer Sheets (Images)", type=['jpg', 'png', 'jpeg'], accept_multiple_files=True)
        
        if uploaded_files and st.button("Submit & Evaluate Now"):
            with st.spinner("Strict ICAI Checking in progress..."):
                images = [Image.open(file) for file in uploaded_files]
                
                # Logic: Send Questions + All Images to Gemini
                prompt = [f"Here is the Question Paper: {st.session_state['generated_questions']}. \n\n CHECK these answer sheets STRICTLY as per ICAI standards. For each question attempted, give marks and remarks.", *images]
                
                response = model.generate_content(prompt)
                
                st.markdown("## 📊 Result & Analysis")
                st.markdown(response.text)
                
        if st.button("Reset / New Test"):
            st.session_state['generated_questions'] = None
            st.rerun()

# ==========================================
# 6️⃣ FEATURE: EXTERNAL CHECKER (Q + A Upload)
# ==========================================
elif st.session_state['current_page'] == "ExternalCheck":
    st.title("📸 External Answer Analysis")
    st.write("Check answers for questions from ANY source (Books, RTP, MTP).")
    
    col1, col2 = st.columns(2)
    with col1:
        q_img = st.file_uploader("Upload Question Image", type=['jpg', 'png'])
    with col2:
        a_img = st.file_uploader("Upload Your Answer Image", type=['jpg', 'png'])
        
    if q_img and a_img:
        if st.button("Analyze My Answer"):
            with st.spinner("Analyzing..."):
                img1 = Image.open(q_img)
                img2 = Image.open(a_img)
                
                prompt = ["Read this Question image and Check this Answer image strictly. Give marks out of 5 and improve the answer.", img1, img2]
                response = model.generate_content(prompt)
                st.markdown(response.text)

# ==========================================
# 7️⃣ FEATURE: ASK KUCHU (Emotional Support)
# ==========================================
elif st.session_state['current_page'] == "Kuchu":
    st.title("🤖 Chat with Kuchu (CA Assistant)")
    
    user_input = st.text_input("Ask a doubt or share your stress...")
    
    if st.button("Send"):
        with st.spinner("Kuchu is thinking..."):
            prompt = f"""
            You are 'Kuchu', a supportive CA Senior.
            User Input: {user_input}
            
            Task:
            1. If it's a technical doubt, explain it simply with an example.
            2. If the user seems stressed/tired, be EMOTIONAL and MOTIVATING. Tell them "You can do it!".
            3. Keep the tone friendly but professional.
            """
            response = model.generate_content(prompt)
            
            st.markdown('<div class="kuchu-msg">', unsafe_allow_html=True)
            st.markdown(f"**Kuchu:** {response.text}")
            st.markdown('</div>', unsafe_allow_html=True)
