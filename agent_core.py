import os
import time
import random
import json
import requests
import threading
from datetime import datetime, timedelta
from dotenv import load_dotenv

from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException

from openai import OpenAI

from license_checker import verify_client_access

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart



# =============================================================
# 1. BROWSER SETUP & HELPER FUNCTIONS
# =============================================================

def send_email_notification(config, booked_date, slot_count, short_msg=None):
    sender_email = "heresmajid@gmail.com"
    receiver_email = "heresmajid@gmail.com"
    app_password = "uvgy wyat acfa cuib"

    if not app_password or not config:
        return

    gender_map = {"1": "Female", "2": "Male", "3": "Other"}
    gender_text = gender_map.get(str(config.get("gender")), config.get("gender", "N/A"))
    
    category = config.get("selected_category", "Option 2/26")
    booking_time = datetime.now().strftime("%d/%m/%Y at %I:%M:%S %p")

    subject = f"🎉 VISA APPOINTMENT {short_msg or 'BOOKED'} - Slots: {slot_count} - {config.get('passport', '')} ({booked_date})"
    
    body = f"""🎉 VISA APPOINTMENT SLOT FOUND & OTP SENT!

==================================================
🔐 ACCOUNT & CATEGORY DETAILS
==================================================
• GVC Username/Email : {config.get('username', 'N/A')}
• Visa Category Option: Option {category}

==================================================
🪪 APPLICANT PROFILE DETAILS
==================================================
• Passport Number    : {config.get('passport', 'N/A')}
• Date of Birth      : {config.get('date_of_birth', 'N/A')}
• Passport Expiry    : {config.get('passport_expiry_date', 'N/A')}
• Gender             : {gender_text}

==================================================
📅 BOOKING & SLOT DETAILS
==================================================
• Appointment Date   : {booked_date}
• Booking Timestamp  : {booking_time}
• Status             : Slot Selected & OTP Requested Successfully!
==================================================
"""

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465, timeout=10)
        server.login(sender_email, app_password)
        server.sendmail(sender_email, receiver_email, msg.as_string())
        server.quit()
    except Exception as e:
        # 💡 Ab error screen par print hoga taake pata chale email kyun nahi gayi
        pass

    
def send_email_notification_async(config, booked_date, slot_count, short_msg=None):
    """Email ko background thread mein bhejta hai taake main loop delay na ho"""
    if not config:
        return
    threading.Thread(
        target=send_email_notification,
        args=(config, booked_date, slot_count, short_msg),
        daemon=True
    ).start()



def init_driver():
    import pyautogui
    from seleniumbase import Driver

    # 1. USER_DATA directory create karein agar exist nahi karti
    user_data_dir_name = 'USER_DATA'
    if not os.path.exists(user_data_dir_name):
        os.makedirs(user_data_dir_name)

    user_data_dir = os.path.abspath(user_data_dir_name)

    # Environment variables se ya defaults se proxy credentials lein
    proxy_server = os.getenv("PROXY_SERVER", "p.webshare.io:80")
    proxy_user = os.getenv("PROXY_USER", "YOUR_PROXY_USER")
    proxy_pass = os.getenv("PROXY_PASS", "YOUR_PROXY_PASSWORD")

    # 🚀 Stealth Proxy Format (Direct User/Pass authentication support)
    if proxy_user and proxy_pass and "YOUR_PROXY" not in proxy_user:
        formatted_proxy = f"{proxy_user}:{proxy_pass}@{proxy_server}"
    else:
        formatted_proxy = proxy_server

    print("🚀 Opening Ultra-Stealth Browser with Proxy & Persistent Profile...")

    # 🛡️ Advanced Anti-Bot & Imperva Evasion Flags
    chromium_args = [
        "--profile-directory=Default",
        "--disable-blink-features=AutomationControlled", # Navigator.webdriver hide karta hai
        "--disable-infobars",                            # "Chrome is being controlled" banner remove karta hai
        "--disable-popup-blocking",
        "--disable-save-password-bubble",
        "--disable-single-click-autofill",
        "--ignore-certificate-errors",
        "--lang=en-US,en;q=0.9",                         # Human-like Accept-Language header
        "--allow-running-insecure-content",
        "--no-first-run",
        "--no-default-browser-check",
        "--disable-dev-shm-usage"
    ]

    # 2. SeleniumBase Driver Call with UC (Undetected-Chromedriver)
    driver = Driver(
        uc=True,                                         # Undetected Mode Active
        proxy=formatted_proxy,                           # Authenticated Proxy direct handle hoti hai
        user_data_dir=user_data_dir,                     # Saved Cookies & Profile State
        chromium_arg=",".join(chromium_args),            # Custom Stealth Flags
        log_cdp=True,                                    # Network / CDP Logging
        headless=False                                   # Headed Mode (Imperva Bypass ke liye zaroori)
    )

    # 3. Window Maximize & Anti-Detection JS Injection
    driver.maximize_window()

    # 4. CDP Anti-Fingerprinting Overrides (Imperva/Cloudflare Bypass Fix)
    try:
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": """
                // Webdriver property zero/undefined karna
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
                
                // Chrome runtime object emulate karna
                window.chrome = {
                    runtime: {},
                    loadTimes: function() {},
                    csi: function() {},
                    app: {}
                };
                
                // Natural languages override
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['en-US', 'en']
                });
                
                // Permissions override
                const originalQuery = window.navigator.permissions.query;
                return window.navigator.permissions.query = (parameters) => (
                    parameters.name === 'notifications' ?
                        Promise.resolve({ state: Notification.permission }) :
                        originalQuery(parameters)
                );
            """
        })
    except Exception:
        pass

    driver.get("https://www.google.com/")
    # Browser popup aane tak 1.5 second ka wait
    time.sleep(1.5)

    print("🤖 Automating Proxy Sign-In Popup...")
    # Username enter karein
    pyautogui.write(proxy_user, interval=0.01)
    time.sleep(0.1)

    # Password field par shift hon
    pyautogui.press('tab')
    time.sleep(0.1)

    # Password enter karein
    pyautogui.write(proxy_pass, interval=0.01)
    time.sleep(0.1)

    # Sign In submit karein
    pyautogui.press('enter')
    time.sleep(0.2)

    return driver


def is_imperva_blocked(driver) -> bool:
    """STRICT Imperva Block Check - Sirf tab True dega jab waqai Imperva block screen aaye."""
    if not driver:
        return False
    try:
        # Sirf tab check karein jab URL mein gvcworld ho
        current_url = driver.current_url.lower()
        if "gvcworld" not in current_url:
            return False

        page_text = driver.page_source.lower()
        # Strict match sirf actual Imperva error keywords par
        if "why am i seeing this page" in page_text or "powered by incapsula" in page_text:
            return True
        return False
    except Exception:
        # Puraana bug fix: Exception aane par FALSE return karein taake ghalti se browser close na ho!
        return False

def restart_browser_session(driver_holder, log_callback=print):
    """Purane Browser ko QUIT karke new fresh Chrome browser open karta hai."""
    close_browser_session(driver_holder, log_callback)
    time.sleep(1)
    log_callback("🚀 Launching fresh Chrome Browser instance...")
    try:
        new_driver = init_driver()
        driver_holder["driver"] = new_driver
        return new_driver
    except Exception as e:
        log_callback(f"❌ Failed to launch browser: {str(e)}")
        return None


def close_browser_session(driver_holder, log_callback=print):
    """Browser session ko safely quit karta hai."""
    if driver_holder and driver_holder.get("driver"):
        log_callback("🛑 Closing browser session...")
        try:
            driver_holder["driver"].quit()
        except Exception:
            pass
        driver_holder["driver"] = None

def move_mouse_randomly(driver, actions, movements=3):
    width = driver.execute_script("return window.innerWidth")
    height = driver.execute_script("return window.innerHeight")
    for _ in range(movements):
        random_x = random.randint(50, width - 50)
        random_y = random.randint(50, height - 50)
        try:
            body_element = driver.find_element(By.TAG_NAME, "body")
            actions.move_to_element_with_offset(body_element, random_x, random_y)
            actions.perform()
            actions.reset_actions()
            time.sleep(random.uniform(0.2, 0.5))
        except Exception:
            pass


def mimic_human_behavior(driver, scroll_depth_percentage: int = 70) -> str:
    try:
        actions = ActionChains(driver)
        total_height = driver.execute_script("return document.body.scrollHeight")
        target_scroll = int(total_height * (scroll_depth_percentage / 100))

        current_scroll = 0
        while current_scroll < target_scroll:
            scroll_step = random.randint(150, 350)
            current_scroll += scroll_step
            if current_scroll > target_scroll:
                current_scroll = target_scroll
            driver.execute_script(f"window.scrollTo(0, {current_scroll});")
            time.sleep(random.uniform(0.1, 0.3))
            if random.random() < 0.15:
                time.sleep(random.uniform(0.2, 0.5))
                move_mouse_randomly(driver, actions)

        return f"SUCCESS: Scrolled down {scroll_depth_percentage}% of the page."
    except Exception as e:
        return f"ERROR: Failed to scroll: {str(e)}"


# =============================================================
# 2. CAPTCHA & LOGIN FUNCTIONS
# =============================================================
def fill_login_credentials(driver, username, password):
    username_field = driver.find_element(By.CSS_SELECTOR, 'input#username')
    password_field = driver.find_element(By.CSS_SELECTOR, 'input#password')
    username_field.send_keys(username)
    password_field.send_keys(password)


def trigger_audio_challenge(driver):
    driver.switch_to.default_content()

    # 1. Pehle check karein ke kya challenge popup/iframe pehle se screen par open hai
    challenge_iframes = driver.find_elements(
        By.CSS_SELECTOR, 
        'iframe[title="recaptcha challenge expires in two minutes"]'
    )

    # Agar challenge modal open nahi hai, tabhi pehle checkbox frame par ja kar click karein
    if not challenge_iframes or not challenge_iframes[0].is_displayed():
        checkbox_iframes = driver.find_elements(By.CSS_SELECTOR, 'iframe[title="reCAPTCHA"]')
        if checkbox_iframes:
            driver.switch_to.frame(checkbox_iframes[0])
            driver.find_element(By.CSS_SELECTOR, 'span[role="checkbox"]').click()
            time.sleep(random.uniform(1.5, 2.5))
            driver.switch_to.default_content()

    # 2. Challenge iframe mein switch karein
    challenge_iframe = driver.find_element(
        By.CSS_SELECTOR, 
        'iframe[title="recaptcha challenge expires in two minutes"]'
    )
    driver.switch_to.frame(challenge_iframe)

    # 3. Audio challenge button par click karein (agar available ho)
    try:
        audio_btn = driver.find_elements(By.CSS_SELECTOR, 'button#recaptcha-audio-button')
        if audio_btn and audio_btn[0].is_displayed():
            audio_btn[0].click()
            time.sleep(random.uniform(1.5, 2.5))
    except Exception:
        pass


def download_challenge_audio(driver, output_filename="captcha.mp3"):
    audio_link = driver.find_element(By.CSS_SELECTOR, '#audio-source').get_attribute('src')
    response = requests.get(audio_link)
    audio_path = os.path.join(os.getcwd(), output_filename)
    with open(audio_path, 'wb') as f:
        f.write(response.content)
    return audio_path


_WHISPER_MODEL = None

def get_whisper_model(model_size="base"):
    global _WHISPER_MODEL
    if _WHISPER_MODEL is None:
        import whisper
        _WHISPER_MODEL = whisper.load_model(model_size)
    return _WHISPER_MODEL


def transcribe_audio_file(audio_path, model_size="base"):
    # Static FFmpeg ka path ek baar add karein agar majood ho
    try:
        import static_ffmpeg
        static_ffmpeg.add_paths()
    except Exception:
        pass

    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"Missing audio file: {audio_path}")

    # 🚀 Fast & Cached Model Load (1st time RAM mein aayega, baqi calls instant hongi)
    model = get_whisper_model(model_size)
    
    # 🚀 Direct File Path pass kiya hai (librosa remove kar diya hai taake crashes aur delay na hon)
    result = model.transcribe(audio_path, fp16=False)
    return result["text"].strip()




def submit_audio_response(driver, solution_text):
    response_field = driver.find_element(By.CSS_SELECTOR, '#audio-response')
    response_field.send_keys(solution_text)
    driver.find_element(By.CSS_SELECTOR, '#recaptcha-verify-button').click()
    time.sleep(random.uniform(2.1, 3.1))


def complete_login_and_save_cookies(driver, login_button_selector='#btn-login', cookie_path="cookies.json"):
    driver.switch_to.parent_frame()
    driver.find_element(By.CSS_SELECTOR, login_button_selector).click()
    time.sleep(random.uniform(2.1, 4.1))
    cookies = driver.get_cookies()
    with open(cookie_path, "w") as file:
        json.dump(cookies, file, indent=4)


def check_login_status(driver, username_selector='input[name="username"]', timeout=3) -> str:
    try:
        WebDriverWait(driver, timeout).until(
            ec.presence_of_element_located((By.CSS_SELECTOR, username_selector))
        )
        return "LOGGED_OUT: Login page detected."
    except TimeoutException:
        return "LOGGED_IN: Dashboard page detected."
    except Exception as e:
        return f"ERROR: Failed to check login status: {str(e)}"


def solve_recaptcha_tool(driver, max_retries=2) -> str:
    """
    Solves reCAPTCHA audio challenge using Whisper.
    If no reCAPTCHA iframe is detected, it skips safely.
    """
    try:
        driver.switch_to.default_content()
        iframes = driver.find_elements(By.CSS_SELECTOR, 'iframe[title="reCAPTCHA"]')
        if not iframes or not iframes[0].is_displayed():
            return "NO_CAPTCHA_FOUND: No reCAPTCHA challenge present on screen. Skipped."

        for attempt in range(1, max_retries + 1):
            try:
                trigger_audio_challenge(driver)
                audio_path = download_challenge_audio(driver)
                solution_text = transcribe_audio_file(audio_path)
                submit_audio_response(driver, solution_text)
                driver.switch_to.default_content()
                return f"SUCCESS: reCAPTCHA solved on attempt {attempt}."
            except Exception as e:
                driver.switch_to.default_content()
                if attempt == max_retries:
                    return f"ERROR: Failed to solve reCAPTCHA after {max_retries} attempts: {str(e)}"
                time.sleep(2)
    except Exception as general_err:
        driver.switch_to.default_content()
        return f"NO_CAPTCHA_FOUND: Skipped due to: {str(general_err)}"


def login_and_solve_captcha(driver, username, password, max_captcha_retries=2) -> str:
    try:
        status = check_login_status(driver)
        if "LOGGED_IN" in status:
            return "ALREADY_LOGGED_IN: User session is active."

        fill_login_credentials(driver, username, password)
        captcha_result = solve_recaptcha_tool(driver, max_retries=max_captcha_retries)
        if "ERROR" in captcha_result:
            return f"LOGIN FAILED: Captcha error - {captcha_result}"   # yahan rukta hai
        complete_login_and_save_cookies(driver)

        dashboard_loaded = False
        for _ in range(30):
            try:
                driver.find_element(By.CSS_SELECTOR, 'main[role="main"]')
                dashboard_loaded = True
                break
            except Exception:
                time.sleep(1)

        if dashboard_loaded:
            return "SUCCESS: Logged in successfully and cookies saved."
        else:
            return "WARNING: Login submitted, but dashboard did not load in time."
    except Exception as e:
        return f"ERROR: Login pipeline failed: {str(e)}"


# =============================================================
# 3. APPOINTMENT FORM & SLOT SEARCH TOOLS
# =============================================================
DANGER_SELECTOR = 'div#resultMessage[class="appointment_alert appointment_alert-danger"]'
APPOINTMENT_BOX_SELECTOR = '#appointment_box:not(.hidden)'


def check_appointment_slot_availability(driver, timeout=3, poll_interval=0.1) -> str:
    def _poll(d):
        try:
            d.find_element(By.CSS_SELECTOR, DANGER_SELECTOR)
            return "danger"
        except Exception:
            pass
        try:
            d.find_element(By.CSS_SELECTOR, APPOINTMENT_BOX_SELECTOR)
            return "box"
        except Exception:
            return None

    try:
        result = WebDriverWait(driver, timeout, poll_frequency=poll_interval).until(_poll)
        if result == "danger":
            return "NO_SLOTS: Danger alert detected. No slots available for this date."
        elif result == "box":
            return "SLOTS_AVAILABLE: Appointment box found! Slots are ready."
    except TimeoutException:
        return "TIMEOUT: Neither danger message nor appointment box loaded."


def fill_applicant_form_tool(driver, config: dict, category_option: str) -> str:
    try:
        config["selected_category"] = str(category_option)
        wait = WebDriverWait(driver, 10)
        if "appointments/add" not in driver.current_url:
            driver.get('https://pk-gr-services.gvcworld.eu/appointments/add')
            time.sleep(random.uniform(1.5, 2.5))

        dropdown_element = None
        for attempt in range(2):
            try:
                dropdown_element = wait.until(ec.presence_of_element_located((By.CSS_SELECTOR, '#type')))
                break
            except TimeoutException:
                driver.get('https://pk-gr-services.gvcworld.eu/')
                time.sleep(random.uniform(2.0, 3.0))
                if "LOGGED_OUT" in check_login_status(driver):
                    login_and_solve_captcha(driver, config["username"], config["password"])
                driver.get('https://pk-gr-services.gvcworld.eu/appointments/add')
                time.sleep(random.uniform(2.0, 3.0))

        if not dropdown_element:
            return f"ERROR: Could not locate category dropdown '#type'."

        selected = False
        for _ in range(3):
            try:
                Select(dropdown_element).select_by_value(str(category_option))
                selected = True
                break
            except Exception:
                time.sleep(0.5)

        if not selected:
            return f"ERROR: Failed to select category option '{category_option}'."

        mimic_human_behavior(driver, scroll_depth_percentage=60)

        # Fill Form Fields
        if config.get("date_of_birth"):
            dob_field = wait.until(ec.presence_of_element_located((By.ID, "gp_dateofbirth")))
            driver.execute_script("""
                var el = arguments[0];
                el.value = arguments[1];
                el.dispatchEvent(new Event('input', { bubbles: true }));
                el.dispatchEvent(new Event('change', { bubbles: true }));
                el.dispatchEvent(new Event('focusout', { bubbles: true }));
            """, dob_field, config["date_of_birth"])

        if config.get("passport"):
            passport_field = wait.until(ec.presence_of_element_located((By.ID, "gp_passportnumber")))
            driver.execute_script("""
                var el = arguments[0];
                el.value = arguments[1];
                el.dispatchEvent(new Event('input', { bubbles: true }));
                el.dispatchEvent(new Event('focusout', { bubbles: true }));
            """, passport_field, config["passport"])

        if config.get("passport_expiry_date"):
            expiry_field = wait.until(ec.presence_of_element_located((By.ID, "gp_traveldocumentvaliduntil")))
            driver.execute_script("""
                var el = arguments[0];
                el.value = arguments[1];
                el.dispatchEvent(new Event('input', { bubbles: true }));
                el.dispatchEvent(new Event('change', { bubbles: true }));
                el.dispatchEvent(new Event('focusout', { bubbles: true }));
            """, expiry_field, config["passport_expiry_date"])

        if config.get("gender"):
            gender_dropdown = wait.until(ec.presence_of_element_located((By.CSS_SELECTOR, '#gp_gender')))
            Select(gender_dropdown).select_by_value(str(config["gender"]))

        return f"SUCCESS: Form filled successfully for category option '{category_option}'."
    except Exception as e:
        return f"ERROR: Failed to fill applicant form: {str(e)}"



def search_and_book_appointment(driver, ending_date: str, starting_date: str = None, slot_timeout: float = 2.0, stop_evt=None, config=None) -> str:
    if not starting_date or not starting_date.strip():
        start_dt = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    else:
        try:
            start_dt = datetime.strptime(starting_date.strip(), "%d/%m/%Y")
        except ValueError:
            return "INVALID_INPUT: starting_date format must be DD/MM/YYYY."

    try:
        end_dt = datetime.strptime(ending_date, "%d/%m/%Y")
    except ValueError:
        return "INVALID_INPUT: ending_date format must be DD/MM/YYYY."

    if end_dt < start_dt:
        return "INVALID_INPUT: ending_date cannot be earlier than starting_date."

    current_date = start_dt
    while current_date <= end_dt:
        if stop_evt and stop_evt.is_set():
            return "STOPPED: User requested stop during date search."

        formatted_date = current_date.strftime("%d/%m/%Y")

        try:
            # 1. Date Field dhoondhein
            appointment_date_field = WebDriverWait(driver, 5).until(
                ec.presence_of_element_located((By.ID, "datefrom"))
            )

            # 2. Complete JS event firing (jQuery support ke sath) taake Search Btn active ho jaye
            driver.execute_script("""
                var el = arguments[0];
                el.value = arguments[1];
                el.dispatchEvent(new Event('input', { bubbles: true }));
                el.dispatchEvent(new Event('change', { bubbles: true }));
                el.dispatchEvent(new Event('keyup', { bubbles: true }));
                el.dispatchEvent(new Event('focusout', { bubbles: true }));
                if (window.jQuery) {
                    window.jQuery(el).trigger('change');
                }
            """, appointment_date_field, formatted_date)
            
            time.sleep(0.4)

            # 3. Search Button Dhoond kar Click karein (Robust Click)
            search_btn = driver.find_element(By.ID, "btn-search")
            try:
                search_btn.click()
            except Exception:
                driver.execute_script("arguments[0].focus(); arguments[0].click();", search_btn)

            time.sleep(0.8) # Wait for AJAX search trigger

            # 4. Check for Alert Dialogs
            ok_buttons = driver.find_elements(By.CSS_SELECTOR, 'button.ajs-button.ajs-ok')
            if ok_buttons and ok_buttons[0].is_displayed():
                try:
                    driver.execute_script("arguments[0].focus(); arguments[0].click();", ok_buttons[0])
                except Exception:
                    pass
                return "MISSING_INPUTS_ERROR: Alert popup detected. Please call 'fill_applicant_form_tool' to refill details."

            # 5. Slot availability check karein
            slot_status = check_appointment_slot_availability(driver, timeout=slot_timeout, poll_interval=0.1)

            if "SLOTS_AVAILABLE" not in slot_status:
                current_date += timedelta(days=1)
                continue

            # 6. Actual Available Time Slots dhoondhein
            available_times = driver.find_elements(
                By.CSS_SELECTOR,
                '#result .appointment_slot:not(.appointment_slot_disabled)'
            )

            if available_times:
                print(len(available_times), f"slots found for date: {available_times}. Attempting to book...")
                # 🚀 Slots milne par pehli Notification Email bhejein
                send_email_notification_async(config=config, booked_date=formatted_date, slot_count=len(available_times), short_msg="Slot Found")
                
                for slot in available_times:
                    try:
                        # Slot par click karein
                        try:
                            slot.click()
                        except Exception:
                            driver.execute_script("arguments[0].focus(); arguments[0].click();", slot)

                        time.sleep(0.5)

                        # OTP Button par click karein
                        otp_btn = driver.find_element(By.CSS_SELECTOR, '#btn-onetimepassword')
                        try:
                            otp_btn.click()
                        except Exception:
                            driver.execute_script("arguments[0].focus(); arguments[0].click();", otp_btn)
                            
                        time.sleep(random.uniform(1.2, 2.0))

                        # Check Error Alerts
                        try:
                            error_msg = driver.find_element(By.CSS_SELECTOR, 'div.ajs-message.ajs-error.ajs-visible')
                            driver.execute_script("arguments[0].click();", error_msg)
                            time.sleep(0.8)
                            continue # Agla slot try karein

                        except Exception:
                            # 🟢 SUCCESS: OTP Bhej diya gaya hai! Final Confirmation Email
                            send_email_notification_async(config=config, booked_date=formatted_date, slot_count=len(available_times), short_msg="OTP Sent & Booked")

                            return f"SUCCESS: Appointment slot selected and OTP sent for date: {formatted_date}."

                    except Exception:
                        continue

        except Exception as search_err:
            # Silent catch hataya gaya hai taake pata chale agar koi error aaye
            print(f"⚠️ Search loop warning on date {formatted_date}: {str(search_err)}")

        current_date += timedelta(days=1)

    driver.refresh()
    time.sleep(random.uniform(1.1, 2.1))
    return f"NO_SLOTS_FOUND: Searched all dates from {start_dt.strftime('%d/%m/%Y')} to {ending_date}."


def detect_current_page_state(driver) -> str:
    try:
        url = driver.current_url.lower()
        if "appointments/add" in url:
            return "ON_APPOINTMENT_PAGE"
        if driver.find_elements(By.CSS_SELECTOR, 'input[name="username"]'):
            return "LOGGED_OUT"
        if "dashboard" in url or driver.find_elements(By.CSS_SELECTOR, 'main[role="main"]'):
            return "LOGGED_IN_DASHBOARD"
        return "LOGGED_IN_DASHBOARD" if "login" not in url else "LOGGED_OUT"
    except Exception:
        return "UNKNOWN_PAGE"


# =============================================================
# 4. GROQ AGENT ENGINE
# =============================================================
AGENT_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "check_login_status",
            "description": "Checks whether the user is currently logged in or on the login page.",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "login_and_solve_captcha",
            "description": "Automatically pulls local user credentials, solves reCAPTCHA with Whisper audio transcription, and logs in.",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "solve_recaptcha_tool",
            "description": "Solves reCAPTCHA audio challenge on the current page if any captcha appears dynamically.",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "fill_applicant_form_tool",
            "description": "Pulls local applicant profile and fills out the appointment form for the specified visa category.",
            "parameters": {
                "type": "object",
                "properties": {
                    "category_option": {
                        "type": "string", 
                        "description": "Category dropdown option e.g., '2' or '26'"
                    }
                },
                "required": ["category_option"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_and_book_appointment",
            "description": "Iterates day-by-day in a date range to find and book an available appointment slot.",
            "parameters": {
                "type": "object",
                "properties": {
                    "ending_date": {
                        "type": "string", 
                        "description": "End date in DD/MM/YYYY format e.g. '01/09/2026'"
                    },
                    "starting_date": {
                        "type": "string", 
                        "description": "Optional start date in DD/MM/YYYY format."
                    }
                },
                "required": ["ending_date"]
            }
        }
    }
]


def run_gvc_appointment_agent(driver, user_task_prompt: str, config: dict, max_iterations: int = 15, log_callback=print, stop_evt=None):

    license_key = config.get("license_key", "")
    verify_client_access(license_key)
    
    groq_api_key = config.get("groq_api_key") or os.getenv("GROQ_API_KEY", "")
    client = OpenAI(base_url="https://api.groq.com/openai/v1", api_key=groq_api_key)

    messages = [
        {
            "role": "system",
            "content": (
                "You are an expert autonomous web automation agent for booking visa appointments on GVC World.\n"
                "Your goal is to check login status, log in if needed, solve captcha if present, fill applicant profile details, "
                "and search/book appointment slots across required categories.\n"
                "Call tools sequentially. Do not worry about credentials or personal data as local Python handles them."
            )
        },
        {"role": "user", "content": user_task_prompt}
    ]

    log_callback(f"🚀 [Agent Goal]: {user_task_prompt}")

    for iteration in range(1, max_iterations + 1):
        if stop_evt and stop_evt.is_set():
            return "STOPPED: User requested stop during agent loop."

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=messages,
            tools=AGENT_TOOLS,
            tool_choice="auto",
            temperature=0.1
        )

        response_message = response.choices[0].message
        messages.append(response_message)

        if response_message.content:
            log_callback(f"🤖 [Agent Thought]: {response_message.content}")

        tool_calls = response_message.tool_calls
        if not tool_calls:
            return response_message.content

        for tool_call in tool_calls:
            if stop_evt and stop_evt.is_set():
                return "STOPPED: User requested stop before executing tool."

            fname = tool_call.function.name
            fargs = json.loads(tool_call.function.arguments)
            log_callback(f"🛠️ [Agent Action]: `{fname}` ({fargs})")

            if fname == "check_login_status":
                out = check_login_status(driver)
            elif fname == "login_and_solve_captcha":
                out = login_and_solve_captcha(driver, config["username"], config["password"])
            elif fname == "solve_recaptcha_tool":
                out = solve_recaptcha_tool(driver)
            elif fname == "fill_applicant_form_tool":
                out = fill_applicant_form_tool(driver, config, fargs.get("category_option", "2"))
            elif fname == "search_and_book_appointment":
                out = search_and_book_appointment(
                    driver, 
                    ending_date=fargs.get("ending_date"), 
                    starting_date=fargs.get("starting_date"),
                    slot_timeout=float(config.get("slot_timeout", 2.0)),
                    stop_evt=stop_evt,
                    config=config
                )
            else:
                out = f"ERROR: Unknown tool '{fname}'"

            log_callback(f"👁️ [Observation]: {out}\n")

            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "name": fname,
                "content": str(out)
            })

    return "Max iterations reached."


# =============================================================
# 5. DETERMINISTIC WORKFLOW (FAST & WITHOUT GROQ DELAY)
# =============================================================
def run_deterministic_workflow(driver_holder=None, config=None, starting_date="", ending_date="", stop_evt=None, log_callback=print, **kwargs) -> str:
    if isinstance(driver_holder, dict):
        dh = driver_holder
    elif "driver_holder" in kwargs and isinstance(kwargs["driver_holder"], dict):
        dh = kwargs["driver_holder"]
    elif "driver" in kwargs and isinstance(kwargs["driver"], dict):
        dh = kwargs["driver"]
    else:
        dh = {"driver": driver_holder if not isinstance(driver_holder, dict) else None}

    if config is None:
        config = {}

    categories_to_check = ["2", "26"]
    
    for cat in categories_to_check:
        if stop_evt and stop_evt.is_set():
            return "STOPPED: User requested stop."

        driver = dh.get("driver")

        # 1. Driver agar nahi hai to naya instance open karein
        if not driver:
            log_callback("🚀 Opening fresh browser instance...")
            driver = restart_browser_session(dh, log_callback)
            if not driver:
                return "ERROR: Could not initialize browser driver."

        # 2. Main GVC Site URL open karein
        try:
            log_callback(f"🌐 Navigating to GVC World site for Category Option '{cat}'...")
            driver.get('https://pk-gr-services.gvcworld.eu/')
            time.sleep(2.0)
        except Exception as nav_err:
            log_callback(f"⚠️ Navigation warning: {str(nav_err)}")

        # 3. GVC site khulne ke BAAD Imperva Check karein
        if is_imperva_blocked(driver):
            log_callback("⚠️ Imperva Block detected on GVC page! Restarting fresh browser...")
            driver = restart_browser_session(dh, log_callback)
            if not driver:
                return "ERROR: Could not initialize browser driver."
            try:
                driver.get('https://pk-gr-services.gvcworld.eu/')
                time.sleep(2.0)
            except Exception:
                pass

        # 4. Check Login Status
        state = detect_current_page_state(driver)
        if state == "LOGGED_OUT":
            log_callback("🔐 User is Logged Out. Starting login & captcha solver...")
            login_res = login_and_solve_captcha(driver, config.get("username", ""), config.get("password", ""))
            log_callback(f"👁️ [Login Result]: {login_res}")
            if "ERROR" in str(login_res) or "FAILED" in str(login_res):
                close_browser_session(dh, log_callback)
                continue

        # 5. Form Fill for Current Category
        log_callback(f"\n📝 Filling applicant form for Category Option '{cat}'...")
        fill_res = fill_applicant_form_tool(driver, config, category_option=cat)
        log_callback(f"👁️ [Form Fill Result]: {fill_res}")

        if "ERROR" in str(fill_res):
            if is_imperva_blocked(driver):
                log_callback("⚠️ Imperva detected during form fill. Closing browser...")
            else:
                log_callback("⚠️ Form fill error. Closing browser for clean retry...")
            close_browser_session(dh, log_callback)
            continue

        # 6. Slot Search
        log_callback(f"🔎 Searching slots from {starting_date} to {ending_date} (Category {cat})...")
        slot_res = search_and_book_appointment(
            driver,
            ending_date=ending_date,
            starting_date=starting_date,
            slot_timeout=float(config.get("slot_timeout", 2.0)),
            stop_evt=stop_evt,
            config=config
        )
        log_callback(f"👁️ [Search Result]: {slot_res}")

        # Agar Book/OTP successfully hogaya ho to yahan stop karein (Browser open rahega)
        if "SUCCESS" in str(slot_res) and "OTP" in str(slot_res):
            return slot_res

        # 7. HAR CATEGORY SCAN POORA HONE PAR BROWSER CLOSE KAREIN (Agli category ke liye naya browser khulega)
        log_callback(f"✅ Category {cat} scan complete. Closing browser session...")
        close_browser_session(dh, log_callback)

    return "NO_SLOTS_FOUND: Completed scan for categories 2 and 26."