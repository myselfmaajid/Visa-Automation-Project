import streamlit as st
import threading
import queue
import time
import random
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

# .env file se variables load karne ke liye
load_dotenv(override=True)

# Page Setup
st.set_page_config(
    page_title="GVC Visa Appointment Bot",
    page_icon="🤖",
    layout="wide"
)

if "driver_holder" not in st.session_state:
    st.session_state.driver_holder = {"driver": None}

driver_holder = st.session_state.driver_holder

# Custom Styling
st.markdown("""
    <style>
    .main-title { font-size: 2.2rem; font-weight: bold; color: #1E88E5; }
    .status-badge { padding: 8px 15px; border-radius: 8px; font-weight: bold; display: inline-block; }
    .running { background-color: #E8F5E9; color: #2E7D32; border: 1px solid #A5D6A7; }
    .stopped { background-color: #FFEBEE; color: #C62828; border: 1px solid #EF9A9A; }
    </style>
""", unsafe_allow_html=True)

st.markdown("<div class='main-title'>🤖 GVC World Visa Appointment Bot</div>", unsafe_allow_html=True)
st.caption("Autonomous AI Agent for 24/7 Visa Appointment Booking")

# =============================================================
# THREAD-SAFE GLOBAL QUEUE & STATE
# =============================================================
if "log_queue" not in st.session_state:
    st.session_state.log_queue = queue.Queue()

if "logs" not in st.session_state:
    st.session_state.logs = []

if "bot_running" not in st.session_state:
    st.session_state.bot_running = False
    
if "bot_thread" not in st.session_state:
    st.session_state.bot_thread = None

if "cycle_count" not in st.session_state:
    st.session_state.cycle_count = 0

# Global Stop Flag for Thread
if "stop_event" not in st.session_state:
    st.session_state.stop_event = threading.Event()
stop_event = st.session_state.stop_event

def thread_safe_log(msg):
    """Thread-safe logging function that pushes messages to Queue"""
    timestamp = time.strftime("[%H:%M:%S]")
    st.session_state.log_queue.put(f"{timestamp} {msg}")

# -------------------------------------------------------------
# SIDEBAR CONTROLS
# -------------------------------------------------------------
with st.sidebar:
    st.header("⚙️ Bot Settings")
    
    groq_api_key = st.text_input("Groq API Key", value=os.getenv("GROQ_API_KEY", ""), type="password")
    
    license_key = st.text_input(
      "License Key", value=os.getenv("LICENSE_KEY", ""), type="password"
    )
    
    today_date = datetime.now().strftime("%d/%m/%Y")
    default_ending_date = (datetime.now() + timedelta(days=30)).strftime("%d/%m/%Y")

    starting_date = st.text_input("Starting Date (DD/MM/YYYY)", value=today_date)
    ending_date = st.text_input("Target End Date (DD/MM/YYYY)", value=default_ending_date)

    slot_timeout = st.number_input(
        "Slot Search Timeout (Seconds)", 
        min_value=0.5, 
        max_value=10.0,
        value=2.0, 
        step=0.5,
        help="Calendar date search ke result ka wait time (seconds me)."
    )
    
    st.divider()
    st.markdown("### 📊 Status")
    if st.session_state.bot_running:
        st.markdown("<div class='status-badge running'>🟢 Running</div>", unsafe_allow_html=True)
    else:
        st.markdown("<div class='status-badge stopped'>🔴 Bot Stopped</div>", unsafe_allow_html=True)

# -------------------------------------------------------------
# MAIN FORM INPUTS
# -------------------------------------------------------------
col1, col2 = st.columns(2)

with col1:
    st.subheader("🔐 Account Credentials")
    username = st.text_input("GVC Username / Email", value=os.getenv("GVC_USERNAME", ""))
    password = st.text_input("GVC Password", value=os.getenv("GVC_PASSWORD", ""), type="password")

with col2:
    st.subheader("🪪 Applicant Profile Details")
    dob = st.text_input("Date of Birth (DD/MM/YYYY)", value=os.getenv("dob", ""))
    passport = st.text_input("Passport Number", value=os.getenv("passport", ""))
    passport_expiry = st.text_input("Passport Expiry Date (DD/MM/YYYY)", value=os.getenv("passport_expiry", ""))
    gender = st.selectbox("Gender", options=["1", "2", "3"], format_func=lambda x: {"1": "Female", "2": "Male", "3": "Other"}[x], index=1)

st.divider()

# -------------------------------------------------------------
# 24/7 BOT THREAD WORKER (100% Thread-Safe)
# -------------------------------------------------------------
def bot_thread_worker(config, starting_date, ending_date, stop_evt, log_q, driver_holder):
    from license_checker import verify_client_access
    
    try:
        verify_client_access(config.get("license_key"))
    except Exception as err:
        log_q.put(f"❌ CRITICAL: License verification failed - {str(err)}")
        return
    
    from agent_core import run_deterministic_workflow
    
    if not starting_date.strip():
        starting_date = datetime.now().strftime("%d/%m/%Y")
        
    def worker_log(msg):
        timestamp = time.strftime("[%H:%M:%S]")
        log_q.put(f"{timestamp} {msg}")

    booking_successful = False

    try:
        cycle_count = 0
        while not stop_evt.is_set():
            cycle_count += 1
            worker_log(f"\n--- 🔄 Starting Fast Search Cycle #{cycle_count} ---")

            # 🚀 Dynamic Workflow Call
            result = run_deterministic_workflow(
                driver_holder=driver_holder,
                config=config,
                starting_date=starting_date,
                ending_date=ending_date,
                stop_evt=stop_evt,
                log_callback=worker_log
            )

            if stop_evt.is_set():
                worker_log("🛑 Execution stopped by user request.")
                break

            if "SUCCESS" in str(result) and "OTP" in str(result):
                worker_log("🎉🎉🎉 APPOINTMENT BOOKED SUCCESSFULLY! 🎉🎉🎉")
                booking_successful = True
                break
            
            time.sleep(0.1)

    except Exception as e:
        worker_log(f"⚠️ Bot Interrupted / Error: {str(e)}")
    finally:
        active_driver = driver_holder.get("driver")
        if not booking_successful:
            if active_driver:
                try:
                    active_driver.quit()
                except Exception:
                    pass
            driver_holder["driver"] = None
            worker_log("🛑 Chrome Driver Session Closed.")
        else:
            worker_log("🟢 Browser left OPEN for manual OTP / Final Confirmation.")
# -------------------------------------------------------------
# BUTTONS & UI CONTROLS
# -------------------------------------------------------------
btn_col1, btn_col2 = st.columns([1, 4])

with btn_col1:
    if not st.session_state.bot_running:
        if st.button("🚀 START 24/7 BOT", type="primary", use_container_width=True):
            if not username or not password:
                st.error("Please provide Username, and Password!")
            else:
                st.session_state.bot_running = True
                st.session_state.cycle_count = 0
                st.session_state.logs = ["🚀 Bot starting..."]
                
                stop_event.clear()

                config = {
                    "license_key": license_key,
                    "groq_api_key": groq_api_key,
                    "username": username,
                    "password": password,
                    "date_of_birth": dob,
                    "passport": passport,
                    "passport_expiry_date": passport_expiry,
                    "gender": gender,
                    "slot_timeout": slot_timeout
                }
                
                t = threading.Thread(
                    target=bot_thread_worker, 
                    args=(config, starting_date, ending_date, stop_event, st.session_state.log_queue, driver_holder),
                    daemon=True
                )
                
                st.session_state.bot_thread = t

                t.start()
                st.rerun()
    else:
        if st.button("🛑 STOP BOT", type="secondary", use_container_width=True):
            stop_event.set()
            st.session_state.bot_running = False
            
            # Instantly Close Chrome Browser window
            if driver_holder.get("driver"):
                try:
                    driver_holder["driver"].quit()
                except Exception:
                    pass
                driver_holder["driver"] = None

            st.session_state.logs.append("🛑 Stop request sent! Closing Chrome & terminating bot worker...")
            st.rerun()

# -------------------------------------------------------------
# PULL LOGS FROM THREAD-SAFE QUEUE TO STREAMLIT UI
# -------------------------------------------------------------
MAX_LOG_HISTORY = 5 # Sirf last 30 logs rakhein

while not st.session_state.log_queue.empty():
    msg = st.session_state.log_queue.get()
    st.session_state.logs.append(msg)

# ✂️ Extra logs ko trim kar dein taake RAM full na ho
if len(st.session_state.logs) > MAX_LOG_HISTORY:
    st.session_state.logs = st.session_state.logs[-MAX_LOG_HISTORY:]

st.subheader("🖥️ Live Execution Terminal Logs")
log_container = st.empty()
log_text = "\n".join(st.session_state.logs[-35:])  # Last 35 logs
log_container.code(log_text if log_text else "Bot is currently idle. Click 'START 24/7 BOT' to begin.", language="bash")

if st.session_state.bot_thread is not None:
    if not st.session_state.bot_thread.is_alive():
        st.session_state.bot_running = False
        st.session_state.bot_thread = None
        st.rerun()

# Auto-Rerun UI while bot is running to show live streaming logs
if st.session_state.bot_running:
    time.sleep(1.0)
    st.rerun()