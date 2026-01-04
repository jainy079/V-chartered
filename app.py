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
# 🛡️ SECURE SETUP (Sirf ye hissa badalna hai)
# ==========================================
try:
    # Hum check karenge ki kya Key "Secrets" mein hai?
    if "GOOGLE_API_KEY" in st.secrets:
        genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
        model = genai.GenerativeModel('gemini-2.5-flash')
    else:
        # Agar key nahi mili toh ye error dikhega
        st.error("🚨 Error: API Key nahi mili! Streamlit Secrets check karo.")
        st.stop()
except Exception as e:
    st.error(f"Connection Error: {e}")

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="V-Chartered Pro",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- SUBJECT LISTS ---
CA_FINAL_SUBJECTS = ["Financial Reporting (FR)", "Advanced Financial Management (AFM)", "Advanced Auditing", "Direct Tax", "Indirect Tax (GST)", "IBS"]
CA_INTER_SUBJECTS = ["Advanced Accounting", "Corporate Laws", "Taxation", "Costing", "Auditing", "FM-SM"]

# ==========================================
# 🎨 CUSTOM CSS (PROFESSIONAL UI)
# ==========================================
st.markdown("""
<style>
    /* Global Background */
    .stApp { background-color: #F0F4F8; }
    
    /* 1. SPLASH SCREEN STYLES */
    .splash-container {
        display: flex; flex-direction: column; align-items: center; justify-content: center; height: 80vh;
    }
    .splash-title {
        font-size: 80px !important; font-weight: 900; color: #004B87; 
        text-align: center; margin-bottom: 0px; text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
    }
    .splash-subtitle {
        font-size: 24px; color: #555; text-align: center; margin-bottom: 40px;
    }
    .splash-credits {
        font-size: 16px; color: #888; text-align: center; font-style: italic; margin-top: 50px;
    }

    /* 2. CARD STYLES */
    .feature-card {
        background-color: white; padding: 25px; border-radius: 15px;
        box-shadow: 0 10px 20px rgba(0,0,0,0.08); text-align: center;
        border: 1px solid #E1E8ED; margin-bottom: 20px; transition: all 0.3s ease;
    }
    .feature-card:hover { transform: translateY(-5px); border-color: #004B87; box-shadow: 0 15px 30px rgba(0,75,135,0.15); }
    .feature-icon { font-size: 40px; margin-bottom: 10px; }
    
    /* 3. BUTTONS */
    .stButton>button {
        background-color: #004B87; color: white; border-radius: 8px; font-weight: 600;
        width: 100%; border: none; padding: 12px;
    }
    .stButton>button:hover { background-color: #003366; }

    /* 4. LEADERBOARD & CHAT */
    .lb-row {
        background: white; padding: 12px; margin: 5px 0; border-radius: 8px;
        border-left: 4px solid #004B87; box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        font-size: 14px;
    }
    .kuchu-bubble {
        background-color: #E3F2FD; border-radius: 15px; padding: 15px;
        border-bottom-left-radius: 2px; border: 1px solid #BBDEFB; margin-top: 10px;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 💾 DATABASE & AUTH FUNCTIONS
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

def get_user_history(email):
    conn = sqlite3.connect('vchartered_db.db')
    df = pd.read_sql_query(f"SELECT subject, score, date FROM results WHERE email='{email}'", conn)
    conn.close()
    return df

init_db()

# ==========================================
# ✨ 1. SPLASH SCREEN (FIXED & ANIMATED)
# ==========================================
if 'splash_shown' not in st.session_state:
    placeholder = st.empty()
    with placeholder.container():
        st.markdown('<div class="splash-container">', unsafe_allow_html=True)
        st.markdown('<div class="splash-title">V-Chartered</div>', unsafe_allow_html=True)
        st.markdown('<div class="splash-subtitle">Redefining CA Preparation</div>', unsafe_allow_html=True)
        # 👇 TERA NAAM & CREDITS 👇
        st.markdown('<div class="splash-credits">Made by <b>Atishay Jain</b> & <b>Google Gemini Services</b></div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        bar = st.progress(0)
        for i in range(100):
            time.sleep(0.015)
            bar.progress(i + 1)
        time.sleep(1)
        
    placeholder.empty()
    st.session_state['splash_shown'] = True

# ==========================================
# 🔐 LOGIN LOGIC (COOKIE FIXED)
# ==========================================
cookie_manager = stx.CookieManager(key="secure_auth")

if 'user_name' not in st.session_state: st.session_state['user_name'] = None
if 'user_email' not in st.session_state: st.session_state['user_email'] = None
if 'current_page' not in st.session_state: st.session_state['current_page'] = "Home"

# Cookie Auto-Login
cookie_email = cookie_manager.get(cookie='v_email')
cookie_user = cookie_manager.get(cookie='v_user')

if cookie_email and not st.session_state['user_email']:
    st.session_state['user_email'] = cookie_email
    st.session_state['user_name'] = cookie_user

# Show Login if not logged in
if not st.session_state['user_email']:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<h2 style='text-align:center; color:#004B87;'>Login Required</h2>", unsafe_allow_html=True)
        tab1, tab2 = st.tabs(["🔐 Login", "📝 Sign Up (Gmail)"])
        
        with tab1:
            email = st.text_input("Email ID")
            password = st.text_input("Password", type="password")
            if st.button("Login Securely"):
                user = check_login(email, password)
                if user:
                    cookie_manager.set('v_email', email, expires_at=datetime.datetime.now() + datetime.timedelta(days=30), key="set_e")
                    cookie_manager.set('v_user', user, expires_at=datetime.datetime.now() + datetime.timedelta(days=30), key="set_u")
                    st.session_state['user_email'] = email
                    st.session_state['user_name'] = user
                    st.rerun()
                else: st.error("Invalid Credentials")
        
        with tab2:
            new_email = st.text_input("Enter Gmail")
            new_name = st.text_input("Full Name")
            new_pass = st.text_input("Set Password", type="password")
            if st.button("Create Account"):
                if create_user(new_email, new_name, new_pass): st.success("Account Created! Please Login.");
                else: st.error("Email already registered.")
    st.stop()

# ==========================================
# 📊 SIDEBAR (ANALYTICS & NAV)
# ==========================================
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3135/3135715.png", width=60)
    st.markdown(f"### Hi, {st.session_state['user_name']}")
    
   if st.button("Logout"):
        # 1. Activity Log (Agar tracking on hai)
        try:
            log_activity(st.session_state['user_email'], "Logout", "User Clicked")
        except:
            pass # Agar spy mode nahi hai toh ignore karega
        
        # 2. Cookies Delete (Safe Mode - Crash nahi hoga)
        try:
            cookie_manager.delete('v_email', key="safe_logout_email")
        except:
            pass
            
        try:
            cookie_manager.delete('v_user', key="safe_logout_user")
        except:
            pass
            
        # 3. Session Clear
        st.session_state['user_email'] = None
        st.session_state['user_name'] = None
        st.rerun()
        
    st.markdown("---")
    st.markdown("### 🏆 Leaderboard")
    lb = get_leaderboard()
    if not lb.empty:
        for i, row in lb.iterrows():
            st.markdown(f'<div class="lb-row">🥇 <b>{row["score"]}/50</b><br>{row["email"].split("@")[0]}</div>', unsafe_allow_html=True)
    else: st.caption("No Test Data Yet")

    st.markdown("---")
    st.markdown("### 📈 Performance")
    hist = get_user_history(st.session_state['user_email'])
    if not hist.empty:
        fig = px.bar(hist, x='subject', y='score', color='score', height=200)
        fig.update_layout(margin=dict(l=0,r=0,t=0,b=0), paper_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig, use_container_width=True)
    
    if st.button("🏠 Home"): st.session_state['current_page'] = "Home"; st.rerun()

# ==========================================
# 🏠 HOME PAGE (DASHBOARD)
# ==========================================
if st.session_state['current_page'] == "Home":
    st.title("V-Chartered Dashboard")
    
    c1, c2 = st.columns(2)
    c3, c4 = st.columns(2)
    
    with c1:
        st.markdown('<div class="feature-card"><div class="feature-icon">📑</div><h3>Mock Test Series</h3><p>10 Q Set | Difficulty Select</p></div>', unsafe_allow_html=True)
        if st.button("Start Mock Test"): st.session_state['current_page'] = "Test"; st.rerun()
    with c2:
        st.markdown('<div class="feature-card"><div class="feature-icon">📸</div><h3>Answer Checker</h3><p>Check Internal & External</p></div>', unsafe_allow_html=True)
        if st.button("Open Scanner"): st.session_state['current_page'] = "Checker"; st.rerun()
    with c3:
        st.markdown('<div class="feature-card"><div class="feature-icon">🤖</div><h3>Kuchu Assistant</h3><p>Doubts & Motivation</p></div>', unsafe_allow_html=True)
        if st.button("Chat with Kuchu"): st.session_state['current_page'] = "Kuchu"; st.rerun()
    with c4:
        st.markdown('<div class="feature-card"><div class="feature-icon">📚</div><h3>Smart Library</h3><p>AI Notes Generator</p></div>', unsafe_allow_html=True)
        if st.button("Open Library"): st.session_state['current_page'] = "Library"; st.rerun()

# ==========================================
# 📑 FEATURE 1: MOCK TEST (10 Questions + Difficulty)
# ==========================================
elif st.session_state['current_page'] == "Test":
    st.title("📑 CA Exam Simulator")
    
    if 'test_paper' not in st.session_state:
        c1, c2, c3 = st.columns(3)
        with c1: level = st.selectbox("Level", ["CA Final", "CA Inter"])
        with c2: subject = st.selectbox("Subject", CA_FINAL_SUBJECTS if level == "CA Final" else CA_INTER_SUBJECTS)
        with c3: diff = st.selectbox("Difficulty", ["Medium", "Hard", "ICAI Tough"])
        
        if st.button("Generate Question Paper (10 Q)"):
            with st.spinner("Generating Paper..."):
                prompt = f"Create a Mock Test Paper for {level} - {subject}. Difficulty: {diff}. Generate exactly 10 QUESTIONS. Mix of MCQ and Descriptive. Total 50 Marks. DO NOT PROVIDE ANSWERS."
                try:
                    res = model.generate_content(prompt)
                    st.session_state['test_paper'] = res.text
                    st.session_state['test_subject'] = subject
                    st.rerun()
                except: st.error("Something went wrong. Try again.")

    else:
        st.markdown(f"### Subject: {st.session_state['test_subject']}")
        with st.expander("📄 View Question Paper", expanded=True):
            st.markdown(st.session_state['test_paper'])
            
        st.markdown("---")
        st.markdown("### 📤 Submit Answer Sheets")
        st.info("Write answers on paper -> Click Photos -> Upload All Here")
        
        files = st.file_uploader("Upload Pages", type=['jpg','png'], accept_multiple_files=True)
        
        if files and st.button("Submit & Check"):
            with st.spinner("Strict Checking in Progress..."):
                imgs = [Image.open(f) for f in files]
                prompt = [f"Here is the QP: {st.session_state['test_paper']}. Check these answer sheets. Give Total Marks out of 50 and Remarks.", *imgs]
                try:
                    res = model.generate_content(prompt)
                    st.markdown(res.text)
                    save_score(st.session_state['user_email'], st.session_state['test_subject'], 35) # Demo score
                except: st.error("Error analyzing images")
                
        if st.button("Reset Test"):
            del st.session_state['test_paper']
            st.rerun()

# ==========================================
# 📸 FEATURE 2: CHECKER (Dual Upload Mode)
# ==========================================
elif st.session_state['current_page'] == "Checker":
    st.title("📸 Answer Checker")
    mode = st.radio("Mode", ["Check External Question (Book/RTP)", "Check My Notes"], horizontal=True)
    
    if "External" in mode:
        c1, c2 = st.columns(2)
        with c1: q_file = st.file_uploader("Upload Question Image", type=['jpg','png'])
        with c2: a_file = st.file_uploader("Upload Answer Image", type=['jpg','png'])
        if q_file and a_file and st.button("Analyze"):
            with st.spinner("Analyzing..."):
                res = model.generate_content(["Read Question, Check Answer strictly.", Image.open(q_file), Image.open(a_file)])
                st.markdown(res.text)
    else:
        f = st.file_uploader("Upload Answer Sheet Only")
        if f and st.button("Check"):
            with st.spinner("Checking..."):
                res = model.generate_content(["Check this answer sheet strictly as per ICAI.", Image.open(f)])
                st.markdown(res.text)

# ==========================================
# 🤖 FEATURE 3: KUCHU BOT (Chat Mode)
# ==========================================
elif st.session_state['current_page'] == "Kuchu":
    st.title("🤖 Chat with Kuchu")
    st.markdown('<div class="kuchu-bubble">👋 Hi! Main Kuchu hoon. Stress ho raha hai ya koi Concept samajhna hai?</div>', unsafe_allow_html=True)
    
    user_input = st.text_input("Message Kuchu...")
    if st.button("Send"):
        with st.spinner("Kuchu thinking..."):
            prompt = f"You are 'Kuchu', a funny, emotional and motivating CA Assistant. User says: {user_input}. If it's a doubt, explain simply. If stress, motivate them heavily."
            res = model.generate_content(prompt)
            st.markdown(f'<div class="kuchu-bubble"><b>Kuchu:</b> {res.text}</div>', unsafe_allow_html=True)

# ==========================================
# 📚 FEATURE 4: SMART LIBRARY (Topic Input)
# ==========================================
elif st.session_state['current_page'] == "Library":
    st.title("📚 Smart Library")
    c1, c2 = st.columns(2)
    with c1: 
        lvl = st.radio("Level", ["CA Final", "CA Inter"], horizontal=True)
        sub = st.selectbox("Subject", CA_FINAL_SUBJECTS if lvl == "CA Final" else CA_INTER_SUBJECTS)
    with c2:
        topic = st.text_input("Enter Topic Name (e.g. Audit Risk)")
        
    if st.button("Generate Notes"):
        if topic:
            with st.spinner("Writing Notes..."):
                res = model.generate_content(f"Create Revision Notes for {lvl} {sub} - {topic}.")
                st.markdown(res.text)
        else: st.warning("Topic missing!")
