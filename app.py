import streamlit as st
import google.generativeai as genai
from PIL import Image
import time
import sqlite3
import hashlib
import pandas as pd
import plotly.express as px
import extra_streamlit_components as stx 
import datetime

# ==========================================
# 🛡️ SECURE SETUP
# ==========================================
try:
    if "GOOGLE_API_KEY" in st.secrets:
        genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
        model = genai.GenerativeModel('gemini-2.5-flash')
    else:
        st.error("🚨 Error: API Key Missing! Streamlit Secrets check karo.")
        st.stop()
except Exception as e:
    st.error(f"Connection Error: {e}")

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="V-Chartered",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- SUBJECT LISTS ---
CA_FINAL_SUBJECTS = ["Financial Reporting (FR)", "Advanced Financial Management (AFM)", "Advanced Auditing", "Direct Tax", "Indirect Tax (GST)", "IBS"]
CA_INTER_SUBJECTS = ["Advanced Accounting", "Corporate Laws", "Taxation", "Costing", "Auditing", "FM-SM"]

# ==========================================
# 🎨 DARK MODE & MOBILE CSS (APP LOOK)
# ==========================================
st.markdown("""
<style>
    /* 1. DARK THEME BACKGROUND */
    .stApp {
        background-color: #0E1117;
        color: #FAFAFA;
    }
    
    /* 2. INPUT FIELDS STYLING (Dark Mode) */
    .stTextInput > div > div > input {
        background-color: #262730;
        color: white;
        border: 1px solid #41444C;
    }
    .stSelectbox > div > div > div {
        background-color: #262730;
        color: white;
    }

    /* 3. APP-STYLE CARDS */
    .feature-card {
        background-color: #1F2937; /* Dark Grey */
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
        text-align: center;
        border: 1px solid #374151;
        margin-bottom: 15px;
    }
    .feature-card h3 {
        color: #60A5FA; /* Light Blue Text */
        font-size: 18px;
        margin-bottom: 5px;
    }
    .feature-card p {
        color: #9CA3AF; /* Grey Text */
        font-size: 14px;
    }
    
    /* 4. BUTTONS (Neon Blue) */
    .stButton>button {
        background-color: #2563EB;
        color: white;
        border-radius: 8px;
        font-weight: 600;
        width: 100%;
        border: none;
        padding: 12px;
    }
    .stButton>button:hover {
        background-color: #1D4ED8;
    }

    /* 5. SPLASH SCREEN (Dark) */
    .splash-title {
        font-size: 60px !important; font-weight: 900; color: #60A5FA; 
        text-align: center; text-shadow: 0px 0px 10px rgba(37, 99, 235, 0.5);
    }
    .splash-subtitle { font-size: 20px; color: #D1D5DB; text-align: center; }
    .splash-credits { font-size: 14px; color: #6B7280; text-align: center; margin-top: 20px; }

    /* 6. ADMIN & CHAT BUBBLES */
    .lb-row {
        background: #111827; padding: 12px; margin: 5px 0; border-radius: 8px;
        border-left: 4px solid #2563EB; color: white;
    }
    .kuchu-bubble {
        background-color: #1E3A8A; color: white; border-radius: 15px; padding: 15px;
        border: 1px solid #2563EB; margin-top: 10px;
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
    c.execute('''CREATE TABLE IF NOT EXISTS activity_logs (email TEXT, action TEXT, details TEXT, timestamp TEXT)''')
    conn.commit()
    conn.close()

def log_activity(email, action, details=""):
    conn = sqlite3.connect('vchartered_db.db')
    c = conn.cursor()
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute("INSERT INTO activity_logs VALUES (?, ?, ?, ?)", (email, action, details, timestamp))
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

def get_logs():
    conn = sqlite3.connect('vchartered_db.db')
    df = pd.read_sql_query("SELECT * FROM activity_logs ORDER BY timestamp DESC", conn)
    conn.close()
    return df

def get_all_users():
    conn = sqlite3.connect('vchartered_db.db')
    df = pd.read_sql_query("SELECT email, username FROM users", conn)
    conn.close()
    return df

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

def get_user_history(email):
    conn = sqlite3.connect('vchartered_db.db')
    df = pd.read_sql_query(f"SELECT subject, score, date FROM results WHERE email='{email}'", conn)
    conn.close()
    return df

init_db()

# ==========================================
# 🍪 LOGIN MANAGER (TOP PRIORITY)
# ==========================================
# Isko sabse upar rakha hai taaki refresh hone par sabse pehle ye load ho
# ==========================================
# 🔐 LOGIN (REFRESH FIX WALA CODE 🛠️)
# ==========================================
cookie_manager = stx.CookieManager(key="spy_auth")

# 👇 YE HAI MAGIC LINE (Refresh problem ka ilaaj)
# Hum code ko aadha second rok rahe hain taaki browser cookie padh sake
time.sleep(0.5)

if 'user_name' not in st.session_state: st.session_state['user_name'] = None
if 'user_email' not in st.session_state: st.session_state['user_email'] = None
if 'current_page' not in st.session_state: st.session_state['current_page'] = "Home"

# Cookie Auto-Login
cookie_email = cookie_manager.get(cookie='v_email')
cookie_user = cookie_manager.get(cookie='v_user')

# Agar cookie mili, toh Session mein daal do (Login Bypass)
if cookie_email and not st.session_state['user_email']:
    st.session_state['user_email'] = cookie_email
    st.session_state['user_name'] = cookie_user
    try:
        log_activity(cookie_email, "Auto-Login", "Refreshed Page")
    except:
        pass
    st.rerun() # Page ko reload karo taaki login dikh jaye

# ==========================================
# 🔐 LOGIN SCREEN (DARK MODE)
# ==========================================
if not st.session_state['user_email']:
    # SPLASH SCREEN (Only on Login Page)
    if 'splash_shown' not in st.session_state:
        placeholder = st.empty()
        with placeholder.container():
            st.markdown('<br><br>', unsafe_allow_html=True)
            st.markdown('<div class="splash-title">V-Chartered</div>', unsafe_allow_html=True)
            st.markdown('<div class="splash-subtitle">Future of CA Preparation</div>', unsafe_allow_html=True)
            st.markdown('<div class="splash-credits">Made by <b>Atishay Jain</b> & <b>Gemini AI</b></div>', unsafe_allow_html=True)
            time.sleep(1.5)
        placeholder.empty()
        st.session_state['splash_shown'] = True

    col1, col2, col3 = st.columns([1, 6, 1])
    with col2:
        st.markdown("<h3 style='text-align:center; color:#60A5FA;'>Login Required</h3>", unsafe_allow_html=True)
        tab1, tab2 = st.tabs(["🔐 Login", "📝 Sign Up"])
        
        with tab1:
            email = st.text_input("Email ID")
            password = st.text_input("Password", type="password")
            if st.button("Login Securely"):
                user = check_login(email, password)
                if user:
                    # Cookies Set with 30 Days Expiry
                    expires = datetime.datetime.now() + datetime.timedelta(days=30)
                    cookie_manager.set('v_email', email, expires_at=expires, key="s_e")
                    cookie_manager.set('v_user', user, expires_at=expires, key="s_u")
                    
                    st.session_state['user_email'] = email
                    st.session_state['user_name'] = user
                    log_activity(email, "Login", "Success")
                    time.sleep(0.5) # Thoda wait taaki cookie set ho jaye
                    st.rerun()
                else:
                    st.error("Invalid Credentials")
                    
        with tab2:
            new_email = st.text_input("Gmail ID")
            new_name = st.text_input("Full Name")
            new_pass = st.text_input("Create Password", type="password")
            if st.button("Create Account"):
                if create_user(new_email, new_name, new_pass): 
                    st.success("Account Created! Login now.")
                    log_activity(new_email, "Sign Up", "New User")
                else: st.error("Email already registered.")
    st.stop()

# ==========================================
# 🕵️‍♂️ ADMIN LOGIC (MISSING THA, AB WAPAS HAI)
# ==========================================
# Check agar email mein 'admin' ya 'atishay' hai
IS_ADMIN = "admin" in st.session_state['user_email'].lower() or "atishay" in st.session_state['user_email'].lower()

# ==========================================
# 📊 SIDEBAR (DARK MODE)
# ==========================================
with st.sidebar:
    st.markdown(f"### 👤 {st.session_state['user_name']}")
    
    if st.button("Logout"):
        try: log_activity(st.session_state['user_email'], "Logout", "User Clicked"); 
        except: pass
        try: cookie_manager.delete('v_email', key="d_e"); 
        except: pass
        try: cookie_manager.delete('v_user', key="d_u"); 
        except: pass
        st.session_state['user_email'] = None
        st.rerun()

    # 👇 YE BUTTON SIRF ADMIN KO DIKHEGA 👇
    if IS_ADMIN:
        st.markdown("---")
        st.markdown("### 🕵️‍♂️ Admin Panel")
        if st.button("View User Logs"):
            st.session_state['current_page'] = "AdminPanel"
            st.rerun()

    st.markdown("---")
    st.markdown("### 🏆 Leaderboard")
    lb = get_leaderboard()
    if not lb.empty:
        for i, row in lb.iterrows():
            st.markdown(f'<div class="lb-row">🥇 <b>{row["score"]}</b> - {row["email"].split("@")[0]}</div>', unsafe_allow_html=True)
    
    if st.button("🏠 Home"): 
        st.session_state['current_page'] = "Home"
        st.rerun()

# ==========================================
# 🏠 HOME PAGE (APP GRID LAYOUT)
# ==========================================
if st.session_state['current_page'] == "Home":
    st.title("Dashboard")
    st.write("Select an option below:")
    
    c1, c2 = st.columns(2)
    c3, c4 = st.columns(2)
    
    with c1:
        st.markdown('<div class="feature-card"><h3>📑 Mock Test</h3><p>Practice Exams</p></div>', unsafe_allow_html=True)
        if st.button("Start Test"): st.session_state['current_page'] = "Test"; log_activity(st.session_state['user_email'], "Visited", "Test"); st.rerun()
    with c2:
        st.markdown('<div class="feature-card"><h3>📸 Checker</h3><p>AI Evaluation</p></div>', unsafe_allow_html=True)
        if st.button("Open Scanner"): st.session_state['current_page'] = "Checker"; log_activity(st.session_state['user_email'], "Visited", "Checker"); st.rerun()
    with c3:
        st.markdown('<div class="feature-card"><h3>🤖 Kuchu</h3><p>AI Assistant</p></div>', unsafe_allow_html=True)
        if st.button("Chat"): st.session_state['current_page'] = "Kuchu"; log_activity(st.session_state['user_email'], "Visited", "Kuchu"); st.rerun()
    with c4:
        st.markdown('<div class="feature-card"><h3>📚 Library</h3><p>Instant Notes</p></div>', unsafe_allow_html=True)
        if st.button("Open Library"): st.session_state['current_page'] = "Library"; log_activity(st.session_state['user_email'], "Visited", "Library"); st.rerun()

# ==========================================
# 🕵️‍♂️ PAGE: ADMIN PANEL (JASOOSI)
# ==========================================
elif st.session_state['current_page'] == "AdminPanel" and IS_ADMIN:
    st.title("🕵️‍♂️ Admin Tracker")
    tab1, tab2 = st.tabs(["📜 Live Logs", "👥 Users"])
    
    with tab1:
        st.write("Live User Activity:")
        logs = get_logs()
        st.dataframe(logs, use_container_width=True)
        if st.button("Refresh Data"): st.rerun()
        
    with tab2:
        users = get_all_users()
        st.dataframe(users, use_container_width=True)

# ==========================================
# 📑 PAGE: MOCK TEST
# ==========================================
elif st.session_state['current_page'] == "Test":
    st.title("Exam Simulator")
    
    if 'test_paper' not in st.session_state:
        c1, c2 = st.columns(2)
        with c1: level = st.selectbox("Level", ["CA Final", "CA Inter"])
        with c2: subject = st.selectbox("Subject", CA_FINAL_SUBJECTS if level == "CA Final" else CA_INTER_SUBJECTS)
        diff = st.selectbox("Difficulty", ["Medium", "Hard", "ICAI Tough"])
        
        if st.button("Generate Paper"):
            with st.spinner("Creating Paper..."):
                prompt = f"Create CA Mock Test for {level} - {subject}. Difficulty: {diff}. 10 Questions. No Answers."
                try:
                    res = model.generate_content(prompt)
                    st.session_state['test_paper'] = res.text
                    st.session_state['test_subject'] = subject
                    log_activity(st.session_state['user_email'], "Generated Test", f"{subject}")
                    st.rerun()
                except: st.error("API Error")
    else:
        st.markdown(f"**Subject:** {st.session_state['test_subject']}")
        with st.expander("📄 Question Paper", expanded=True):
            st.markdown(st.session_state['test_paper'])
        
        st.markdown("---")
        files = st.file_uploader("Upload Answers", accept_multiple_files=True)
        if files and st.button("Submit & Check"):
            with st.spinner("Checking..."):
                imgs = [Image.open(f) for f in files]
                res = model.generate_content([f"Check these answers for: {st.session_state['test_paper']}. Give Marks.", *imgs])
                st.markdown(res.text)
                log_activity(st.session_state['user_email'], "Submitted Test", f"Files: {len(files)}")
        
        if st.button("New Test"):
            del st.session_state['test_paper']
            st.rerun()

# ==========================================
# 📸 PAGE: CHECKER
# ==========================================
elif st.session_state['current_page'] == "Checker":
    st.title("Answer Checker")
    mode = st.radio("Mode", ["External Book/RTP", "My Notes"])
    
    if "External" in mode:
        q = st.file_uploader("Question Img")
        a = st.file_uploader("Answer Img")
        if q and a and st.button("Check"):
            with st.spinner("Analyzing..."):
                res = model.generate_content(["Read Question & Check Answer.", Image.open(q), Image.open(a)])
                st.markdown(res.text)
                log_activity(st.session_state['user_email'], "Used Checker", "External")
    else:
        a = st.file_uploader("Answer Sheet")
        if a and st.button("Check"):
            with st.spinner("Checking..."):
                res = model.generate_content(["Check as ICAI Examiner.", Image.open(a)])
                st.markdown(res.text)
                log_activity(st.session_state['user_email'], "Used Checker", "Internal")

# ==========================================
# 🤖 PAGE: KUCHU
# ==========================================
elif st.session_state['current_page'] == "Kuchu":
    st.title("Kuchu Chat")
    msg = st.text_input("Say something...")
    if st.button("Send"):
        with st.spinner("..."):
            res = model.generate_content(f"You are Kuchu (CA Assistant). Reply to: {msg}")
            st.markdown(f'<div class="kuchu-bubble"><b>Kuchu:</b> {res.text}</div>', unsafe_allow_html=True)
            log_activity(st.session_state['user_email'], "Kuchu Chat", msg)

# ==========================================
# 📚 PAGE: LIBRARY
# ==========================================
elif st.session_state['current_page'] == "Library":
    st.title("Smart Library")
    lvl = st.radio("Level", ["CA Final", "CA Inter"], horizontal=True)
    sub = st.selectbox("Subject", CA_FINAL_SUBJECTS if lvl == "CA Final" else CA_INTER_SUBJECTS)
    topic = st.text_input("Topic")
    
    if st.button("Get Notes"):
        if topic:
            with st.spinner("Fetching..."):
                res = model.generate_content(f"Revision Notes for {lvl} {sub}: {topic}")
                st.markdown(res.text)
                log_activity(st.session_state['user_email'], "Notes Generated", topic)
