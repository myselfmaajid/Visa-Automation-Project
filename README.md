A comprehensive README.md file tailored to document the architecture, components, and workflow of your project:
code
Markdown
# 🤖 GVC World Visa Appointment Bot

An automated software solution designed to scan, monitor, and request visa appointment slots on the GVC World portal (`pk-gr-services.gvcworld.eu`). 

The project features a **Streamlit Web UI**, an **Undetected ChromeDriver engine**, an **Audio reCAPTCHA Solver powered by OpenAI Whisper**, a **Hardware-Bound Licensing System**, and an **LLM-driven Agent fallback (Groq API)**.

---

## 📁 Repository Structure & File Overview

```text
.
├── app.py               # Streamlit Frontend Dashboard & Threading Controller
├── agent_core.py        # Core Browser Automation, Form Manipulation & reCAPTCHA Solver
├── license_checker.py   # Client-side Licensing & HWID Verification Engine
├── server.py            # Server-side Flask API for License Enforcement (PythonAnywhere)
└── README.md            # Technical Documentation
🏗️ System Architecture & Component Analysis
1. app.py — Frontend Dashboard & Execution Manager
Role: User Interface and process controller.
Key Components:
Streamlit UI: Provides inputs for Groq API keys, License Keys, Date Ranges, Slot Timeouts, and Applicant Credentials (DOB, Passport Number, Expiry, Gender).
Thread Safety: Runs the automation loop in a background Python thread (bot_thread_worker) to prevent freezing the UI. Uses a thread-safe queue.Queue to stream live execution logs into the UI log terminal.
Browser Session Lifecycle: Manages driver state (driver_holder) allowing browser sessions to remain open when manual input (like OTP verification) is required upon successful booking.
2. agent_core.py — Automation Core & Intelligence Engine
Role: Controls browser interaction, form completion, slot scanning, audio captcha processing, and notifications.
Key Components:
Browser Initialization (init_driver): Uses undetected_chromedriver with custom Chrome user profiles to reduce automated browser detection signatures.
Human Behavior Emulation: Simulates human-like interactions using random mouse movements (move_mouse_randomly) and variable scrolling steps (mimic_human_behavior).
Automated reCAPTCHA Solver:
Triggers reCAPTCHA's audio challenge.
Downloads the .mp3 challenge payload.
Loads a cached local OpenAI Whisper model (get_whisper_model) to transcribe speech-to-text offline.
Submits the transcribed text into the captcha response input field.
Form Filling & Slot Search:
Dynamically populates input fields (gp_dateofbirth, gp_passportnumber, etc.) using injected JavaScript events (input, change, focusout).
Loops iteratively over specified target dates to query available booking time slots (.appointment_slot).
Email Notifications (send_email_notification_async): Sends background asynchronous SMTP alerts when slots are located or when an OTP is requested.
Deterministic vs. LLM Engine:
run_deterministic_workflow: Fast, low-latency search loop across targeted visa categories (e.g., Options 2 & 26).
run_gvc_appointment_agent: Tool-calling autonomous agent using Groq (llama-3.1-8b-instant) to dynamically evaluate and trigger state actions.
3. license_checker.py — Client-Side License & HWID Validation
Role: Enforces software protection by validating keys against a remote backend.
Key Components:
HWID Generation (get_hwid): Generates a stable hardware signature:
Windows: Reads MachineGuid from HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Cryptography.
Linux/macOS: Combines hostname, processor details, and MAC address via uuid.getnode().
Hashes the raw identifier using SHA-256 (truncated to 16 uppercase characters).
License Check (verify_client_access): Sends a POST request containing license_key and hwid to the licensing server. Access is granted only if approved.
4. server.py — License Verification API Backend
Role: Centralized licensing authority designed for hosting (e.g., PythonAnywhere).
Key Components:
Flask Endpoint (/verify-license): Accepts client validation requests.
Validation Logic:
Checks if the key exists in licenses.json.
Verifies account status (is_active).
Checks expiry date validity (expiry_date).
Enforces HWID Binding: On first run, locks the license key to the client's HWID. Rejects requests from unauthorized hardware signatures unless reset.
🔄 Execution Workflow
code
Mermaid
graph TD
    A[User Launches Streamlit App] --> B[Enter Credentials & License Key]
    B --> C[Click 'Start 24/7 Bot']
    C --> D[license_checker: Verify HWID & Key]
    D -- Unauthorized --> E[Halt Execution & Output Error]
    D -- Authorized --> F[Initialize undetected_chromedriver]
    F --> G[Check Page State & Login Status]
    G -- Logged Out --> H[Fill Credentials & Solve Audio reCAPTCHA via Whisper]
    H --> I[Save Cookies & Load Dashboard]
    G -- Logged In --> I
    I --> J[Select Visa Category & Inject Form Details]
    J --> K[Iterate Through Target Dates]
    K -- Slot Found --> L[Trigger Slot Selection & Request OTP]
    L --> M[Send Async Email Notification]
    M --> N[Leave Browser Open for Manual OTP Entry]
    K -- No Slots --> O[Refresh & Repeat Search Cycle]
⚙️ Setup & Configuration
Environment Variables (.env)
Create a .env file in the root directory:
code
Env
GROQ_API_KEY=your_groq_api_key_here
LICENSE_KEY=your_license_key_here
GVC_USERNAME=your_gvc_login_email
GVC_PASSWORD=your_gvc_login_password
Dependencies
Install the required Python packages:
code
Bash
pip install streamlit selenium undetected-chromedriver requests python-dotenv librosa openai-whisper static-ffmpeg Flask
Running the Application
To start the application dashboard:
code
Bash
streamlit run app.py
🔒 Security Best Practices
Credentials Management: Email app passwords and API keys should strictly be loaded from environment variables (.env) rather than being hardcoded into source files.
HWID Locking: Ensures software access remains restricted to authorized devices only.