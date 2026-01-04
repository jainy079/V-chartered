import streamlit as st
import google.generativeai as genai
from PIL import Image
import time
import sqlite3
import hashlib
import pandas as pd
import extra_streamlit_components as stx # pip install extra-streamlit-components
import datetime

# ==========================================
# 👇 SETUP & CONFIGURATION 👇
# ==========================================
GOOGLE_API_KEY = "AIzaSyCwjIu4Hc4HczJUeZdfVgw1j1VxWPZq-JM"
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash')

st.set_page_config(
    page_title="V-Chartered",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- SUBJECT LISTS ---
CA_FINAL_SUBJECTS = ["Financial Reporting (FR)", "Advanced Financial Management (AFM)", "Advanced Auditing", "Direct Tax", "Indirect Tax (GST)", "IBS"]
CA_INTER_SUBJECTS = ["Advanced Accounting", "Corporate Laws", "Taxation", "Costing", "Auditing", "FM-SM"]

# ==========================================
# 🎨 CUSTOM CSS
# ==========================================
st.markdown("""
<style>
    .stApp { background-color: #f8f9fa; }
    .feature-card {
        background-color: white; padding: 20px; border-radius: 12px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05); text-align: center;
        border: 1px solid #e0e0e0; margin-bottom: 20px;
    }
    .stButton>button {
        background-color: #004B87; color: white; font-weight: 600; border-radius: 8px;
    }
    /* Splash Screen Text Style */
    .splash-title {
        font-size: 60px; font-weight: bold; color: #004B87; text-align: center;
    }
    .splash-subtitle {
        font-size: 20px; color: #555; text-align: center; margin-bottom: 20px;
    }
    .splash-credits {
        font-size: 16px; color: #888; text-align: center; font-style: italic; margin-top: 30px;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 💾 DATABASE FUNCTIONS
# ==========================================
def init_db():
    conn = sqlite3.connect('vchartered_db.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (email TEXT PRIMARY KEY, username TEXT, password TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS results (email TEXT, subject TEXT, score INTEGER, date TEXT)''')
    conn.commit()
    conn.close()

def create_user(email, username, password):
    conn = sqlite3.connect('vchartered_db.db')
    c = conn.cursor()
    hashed_pw = hashlib.sha256(password.encode()).hexdigest()
    try:
        c.execute("INSERT INTO users VALUES (?, ?, ?)", (email, username, hashed_pw))
        conn.commit()
        return True
    except: return False
    finally: conn.close()

def check_login(email, password):
    conn = sqlite3.connect('vchartered_db.db')
    c = conn.cursor()
    hashed_pw = hashlib.sha256(password.encode()).hexdigest()
    c.execute("SELECT username FROM users WHERE email=? AND password=?", (email, hashed_pw))
    result = c.fetchone()
    conn.close()
    return result[0] if result else None

def save_score(email, subject, score):
    conn = sqlite3.connect('vchartered_db.db')
    c = conn.cursor()
    date = datetime.datetime.now().strftime("%Y-%m-%d")
    c.execute("INSERT INTO results VALUES (?, ?, ?, ?)", (email, subject, score, date))
    conn.commit()
    conn.close()

def get_leaderboard():
    conn = sqlite3.connect('vchartered_db.db')
    df = pd.read_sql_query("SELECT email, subject, score FROM results ORDER BY score DESC LIMIT 5", conn)
    conn.close()
    return df

init_db()

# ==========================================
# ✨ SPLASH SCREEN (ANIMATED ENTRY)
# ==========================================
if 'splash_shown' not in st.session_state:
    placeholder = st.empty()
    with placeholder.container():
        st.markdown("<br><br><br>", unsafe_allow_html=True)
        st.markdown('<p class="splash-title">V-Chartered</p>', unsafe_allow_html=True)
        st.markdown('<p class="splash-subtitle">Redefining CA Preparation with AI</p>', unsafe_allow_html=True)
        
        # 👇 TERA NAAM YAHAN HAI 👇
        st.markdown('<p class="splash-credits">Made by <b>Atishay Jain</b> & <b>Google Gemini Services</b></p>', unsafe_allow_html=True)
        
        bar = st.progress(0)
        for i in range(100):
            time.sleep(0.015) # Speed control
            bar.progress(i + 1)
        time.sleep(0.8) # Thoda rukega taaki naam padh sakein
        
    placeholder.empty() # Screen saaf karke aage badho
    st.session_state['splash_shown'] = True

# ==========================================
# 🍪 LOGIN COOKIE MANAGER
# ==========================================
cookie_manager = stx.CookieManager(key="auth_cookie_manager")

if 'user_name' not in st.session_state: st.session_state['user_name'] = None
if 'user_email' not in st.session_state: st.session_state['user_email'] = None
if 'current_page' not in st.session_state: st.session_state['current_page'] = "Home"

cookie_user = cookie_manager.get(cookie='v_user_email')
cookie_name = cookie_manager.get(cookie='v_user_name')

if cookie_user and not st.session_state['user_email']:
    st.session_state['user_email'] = cookie_user
    st.session_state['user_name'] = cookie_name

# ==========================================
# 🔐 AUTH PAGE
# ==========================================
if not st.session_state['user_email']:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<h1 style='text-align: center; color:#004B87;'>Login Required</h1>", unsafe_allow_html=True)
        tab1, tab2 = st.tabs(["Login", "Sign Up"])
        
        with tab1:
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            if st.button("Login"):
                user = check_login(email, password)
                if user:
                    cookie_manager.set('v_user_email', email, expires_at=datetime.datetime.now() + datetime.timedelta(days=30), key="set_email")
                    cookie_manager.set('v_user_name', user, expires_at=datetime.datetime.now() + datetime.timedelta(days=30), key="set_name")
                    st.session_state['user_email'] = email
                    st.session_state['user_name'] = user
                    st.rerun()
                else: st.error("Invalid Credentials")
        
        with tab2:
            new_email = st.text_input("New Email")
            new_name = st.text_input("Full Name")
            new_pass = st.text_input("New Password", type="password")
            if st.button("Create Account"):
                if create_user(new_email, new_name, new_pass): st.success("Created! Login now.")
                else: st.error("Email exists.")
    st.stop()

# ==========================================
# 📊 SIDEBAR
# ==========================================
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3135/3135715.png", width=70)
    st.markdown(f"### 👤 {st.session_state['user_name']}")
    
    if st.button("Logout"):
        cookie_manager.delete('v_user_email', key="del_email")
        cookie_manager.delete('v_user_name', key="del_name")
        st.session_state['user_email'] = None
        st.rerun()
        
    st.markdown("---")
    st.markdown("### 🏆 Leaderboard")
    lb = get_leaderboard()
    if not lb.empty:
        for i, row in lb.iterrows():
            st.markdown(f"🥇 **{row['score']}/5** - {row['email'].split('@')[0]} ({row['subject'][:4]}..)")
    else: st.caption("No Data")
    st.markdown("---")
    if st.button("🏠 Home"): st.session_state['current_page'] = "Home"; st.rerun()

# ==========================================
# 🏠 HOME PAGE
# ==========================================
if st.session_state['current_page'] == "Home":
    st.title(f"Dashboard 🚀")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown('<div class="feature-card"><h3>📚 AI Notes</h3><p>Revision Material</p></div>', unsafe_allow_html=True)
        if st.button("Open Library"): st.session_state['current_page'] = "Material"; st.rerun()
    with c2:
        st.markdown('<div class="feature-card"><h3>📑 Mock Test</h3><p>Take Exam</p></div>', unsafe_allow_html=True)
        if st.button("Start Test"): st.session_state['current_page'] = "Test"; st.rerun()
    with c3:
        st.markdown('<div class="feature-card"><h3>📸 Checker</h3><p>Check Answer</p></div>', unsafe_allow_html=True)
        if st.button("Check Answers"): st.session_state['current_page'] = "Checker"; st.rerun()

# ==========================================
# 📚 PAGE: AI STUDY MATERIAL
# ==========================================
elif st.session_state['current_page'] == "Material":
    st.title("📚 Smart Library")
    level = st.radio("Select Level:", ["CA Final", "CA Inter"], horizontal=True)
    if level == "CA Final": subject = st.selectbox("Search Subject:", CA_FINAL_SUBJECTS)
    else: subject = st.selectbox("Search Subject:", CA_INTER_SUBJECTS)
    topic = st.text_input("Enter Topic Name")
    
    if st.button("Generate Notes"):
        if topic:
            with st.spinner(f"Creating notes..."):
                prompt = f"Create Revision Notes for {level} Subject: {subject}, Topic: {topic}. Include Sections & Case Laws."
                response = model.generate_content(prompt)
                st.markdown(response.text)

# ==========================================
# 📑 PAGE: MOCK TEST
# ==========================================
elif st.session_state['current_page'] == "Test":
    st.title("📝 Exam Simulator")
    c1, c2 = st.columns(2)
    with c1: level = st.selectbox("Level", ["CA Final", "CA Inter"])
    with c2: 
        if level == "CA Final": subject = st.selectbox("Select Subject", CA_FINAL_SUBJECTS)
        else: subject = st.selectbox("Select Subject", CA_INTER_SUBJECTS)
            
    if 'quiz_data' not in st.session_state:
        if st.button("Generate Question"):
            with st.spinner(f"Generating Question..."):
                prompt = f"Create 1 Tough Practical MCQ for {level} - {subject}. Do NOT reveal answer."
                res = model.generate_content(prompt)
                st.session_state['quiz_data'] = res.text
                st.rerun()
    else:
        st.info(st.session_state['quiz_data'])
        ans = st.radio("Your Answer:", ["A", "B", "C", "D"])
        if st.button("Submit"):
            res = model.generate_content(f"Question: {st.session_state['quiz_data']}. User Answer: {ans}. Correct? Give 5 marks if yes, else 0.")
            if "5" in res.text:
                save_score(st.session_state['user_email'], subject, 5)
                st.success("Correct! +5 added.")
            else:
                save_score(st.session_state['user_email'], subject, 0)
                st.error("Incorrect.")
            del st.session_state['quiz_data']
            if st.button("Next"): st.rerun()

# ==========================================
# 📸 PAGE: CHECKER
# ==========================================
elif st.session_state['current_page'] == "Checker":
    st.title("📸 Answer Checker")
    f = st.file_uploader("Upload Image")
    if f and st.button("Check"):
        with st.spinner("Checking..."):
            img = Image.open(f)
            res = model.generate_content(["Check strictly as ICAI Examiner. Give Marks.", img])
            st.markdown(res.text)
