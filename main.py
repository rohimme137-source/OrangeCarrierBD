import time
import re
import requests
import os
import random
import json
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service # Termux Support
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException
import phonenumbers
from phonenumbers import region_code_for_number
import pycountry
import config
import speech_recognition as sr
from pydub import AudioSegment
import io

# --- Python 3.13 Compatibility Patch ---
try:
    import aifc
except ImportError:
    import sys
    from types import ModuleType
    m = ModuleType("aifc")
    m.Error = Exception
    def mock_open(*args, **kwargs): raise NotImplementedError("aifc is removed in Python 3.13")
    m.open = mock_open
    sys.modules["aifc"] = m
# --------------------------------------

active_calls = {}
processing_calls = set()
refresh_pattern_index = 0

# Updated refresh pattern as requested
REFRESH_PATTERN = [1800, 1545, 2110, 1850, 1340]  # seconds

# Heroku-compatible download folder
DOWNLOAD_FOLDER = '/tmp' if os.environ.get('DYNO') else './downloads'
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

def human_like_delay(min_seconds=1, max_seconds=3):
    """Human-like random delay"""
    time.sleep(random.uniform(min_seconds, max_seconds))

def human_like_mouse_movement(driver, element):
    """Simulate human-like mouse movement"""
    try:
        location = element.location
        size = element.size
        offset_x = random.randint(0, size['width'] // 2)
        offset_y = random.randint(0, size['height'] // 2)
        action = ActionChains(driver)
        action.move_to_element_with_offset(element, offset_x, offset_y)
        action.pause(random.uniform(0.1, 0.3))
        action.click()
        action.perform()
    except:
        element.click()

def get_next_refresh_time():
    """Get next refresh time using the specified pattern"""
    global refresh_pattern_index
    interval = REFRESH_PATTERN[refresh_pattern_index]
    refresh_pattern_index = (refresh_pattern_index + 1) % len(REFRESH_PATTERN)
    print(f"[🔄] Next refresh in {interval} seconds ({interval//60} minutes {interval%60} seconds)")
    return interval

def country_to_flag(country_code):
    """Convert country code to flag emoji"""
    if not country_code or len(country_code) != 2:
        return "🏳️"
    return "".join(chr(127397 + ord(c)) for c in country_code.upper())

def detect_country(number):
    """Detect country from phone number"""
    try:
        clean_number = re.sub(r"\D", "", number)
        if clean_number:
            parsed = phonenumbers.parse("+" + clean_number, None)
            region = region_code_for_number(parsed)
            country = pycountry.countries.get(alpha_2=region)
            if country:
                return country.name, country_to_flag(region)
    except:
        pass
    return "Unknown", "🏳️"

def send_message_to_admin(text):
    """Send message to Admin Telegram"""
    try:
        url = f"https://api.telegram.org/bot{config.BOT_TOKEN}/sendMessage"
        payload = {"chat_id": config.ADMIN_CHAT_ID, "text": text, "parse_mode": "Markdown"}
        res = requests.post(url, json=payload, timeout=10)
        if res.ok:
            return res.json().get("result", {}).get("message_id")
    except Exception as e:
        print(f"[❌] Failed to send message to admin: {e}")
    return None

def send_message_to_group(text):
    """Send message to Group Telegram"""
    try:
        url = f"https://api.telegram.org/bot{config.BOT_TOKEN}/sendMessage"
        payload = {"chat_id": config.GROUP_CHAT_ID, "text": text, "parse_mode": "HTML"}
        res = requests.post(url, json=payload, timeout=10)
        if res.ok:
            return res.json().get("result", {}).get("message_id")
    except Exception as e:
        print(f"[❌] Failed to send message to group: {e}")
    return None

def delete_message(chat_id, msg_id):
    """Delete message from Telegram"""
    try:
        url = f"https://api.telegram.org/bot{config.BOT_TOKEN}/deleteMessage"
        requests.post(url, data={"chat_id": chat_id, "message_id": msg_id}, timeout=5)
    except:
        pass

def send_voice_to_group(voice_path, caption):
    """Send voice recording with caption to Group Telegram"""
    try:
        if os.path.getsize(voice_path) < 1000:
            raise ValueError("File too small or empty")
        url = f"https://api.telegram.org/bot{config.BOT_TOKEN}/sendVoice"
        with open(voice_path, "rb") as voice:
            payload = {"chat_id": config.GROUP_CHAT_ID, "caption": caption, "parse_mode": "HTML"}
            files = {"voice": voice}
            response = requests.post(url, data=payload, files=files, timeout=60)
            return response.status_code == 200
    except Exception as e:
        print(f"[❌] Failed to send voice to group: {e}")
    return False

def extract_otp_from_audio(audio_path):
    """Extract OTP from audio file (English + Spanish)"""
    try:
        print(f"[🎯] Attempting OTP extraction from: {audio_path}")
        audio = AudioSegment.from_file(audio_path)
        audio = audio.normalize()
        wav_data = io.BytesIO()
        audio.export(wav_data, format="wav")
        wav_data.seek(0)
        r = sr.Recognizer()
        with sr.AudioFile(wav_data) as source:
            r.adjust_for_ambient_noise(source, duration=0.5)
            audio_data = r.record(source)
        
        try:
            text = r.recognize_google(audio_data, language='en-US')
        except:
            try:
                text = r.recognize_google(audio_data, language='es-ES')
            except:
                return None
        
        otp_patterns = [
            r'\b\d{4,6}\b', r'code[\s\:\-]*(\d{4,6})', r'verification[\s\:\-]*(\d{4,6})',
            r'password[\s\:\-]*(\d{4,6})', r'your[\s]*code[\s]*is[\s]*(\d{4,6})',
            r'código[\s\:\-]*(\d{4,6})', r'verificación[\s\:\-]*(\d{4,6})'
        ]
        
        for pattern in otp_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                otp = matches[0] if isinstance(matches[0], str) else matches[0][0]
                if otp.isdigit(): return otp
        return None
    except:
        return None

def load_cookies_from_config():
    """Load cookies for authentication"""
    try:
        cookies_env = os.environ.get('ORANGE_COOKIES')
        if cookies_env: return json.loads(cookies_env)
        if hasattr(config, 'ORANGE_COOKIES') and config.ORANGE_COOKIES:
            return config.ORANGE_COOKIES
    except: pass
    return []

def setup_chrome_driver_with_cookies():
    """Setup Chrome driver and load cookies"""
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

    is_heroku = os.environ.get('DYNO') is not None
    
    if is_heroku:
        chrome_options.binary_location = os.environ.get('GOOGLE_CHROME_BIN')
        driver_path = os.environ.get('CHROMEDRIVER_PATH')
        driver = webdriver.Chrome(executable_path=driver_path, options=chrome_options)
    else:
        # Termux Path Check
        termux_path = '/data/data/com.termux/files/usr/bin/chromedriver'
        if os.path.exists(termux_path):
            print(f"[🔧] Using Termux Driver: {termux_path}")
            driver = webdriver.Chrome(service=Service(termux_path), options=chrome_options)
        else:
            driver = webdriver.Chrome(options=chrome_options)
    
    cookies = load_cookies_from_config()
    if cookies:
        try:
            driver.get("https://www.orangecarrier.com")
            time.sleep(2)
            driver.delete_all_cookies()
            for cookie in cookies:
                c = cookie.copy()
                if 'expirationDate' in c: c['expiry'] = int(c['expirationDate'])
                for k in ['hostOnly', 'storeId', 'sameSite', 'expirationDate']: c.pop(k, None)
                driver.add_cookie(c)
            driver.refresh()
            time.sleep(3)
        except: pass
    
    driver.set_page_load_timeout(60)
    return driver

def login_with_cookies(driver):
    """Login logic using session"""
    try:
        driver.get(config.LOGIN_URL)
        time.sleep(3)
        if "dashboard" in driver.current_url or "live/calls" in driver.current_url:
            return True
        driver.get(config.CALL_URL)
        time.sleep(3)
        return "login" not in driver.current_url
    except: return False

def extract_calls(driver):
    """Extract call information from the calls table"""
    global active_calls, processing_calls
    try:
        calls_table = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "LiveCalls")))
        rows = calls_table.find_elements(By.TAG_NAME, "tr")
        current_call_ids = set()
        
        for row in rows:
            try:
                row_id = row.get_attribute('id')
                if not row_id: continue
                cells = row.find_elements(By.TAG_NAME, "td")
                if len(cells) < 5: continue
                
                did_number = re.sub(r"\D", "", cells[1].text.strip())
                if not did_number: continue
                current_call_ids.add(row_id)
                
                if row_id not in active_calls:
                    print(f"[📞] New call: {did_number}")
                    country_name, flag = detect_country(did_number)
                    full_url = f"https://www.orangecarrier.com/live/calls/sound?did={did_number}&uuid={row_id}"
                    msg_id = send_message_to_admin(f"📞 {did_number}\n🔗 {full_url}")
                    active_calls[row_id] = {
                        "admin_msg_id": msg_id, "flag": flag, "country": country_name,
                        "did_number": did_number, "call_uuid": row_id,
                        "detected_at": datetime.now(), "full_url": full_url
                    }
            except: continue
        
        for call_id in list(active_calls.keys()):
            if call_id not in current_call_ids and call_id not in processing_calls:
                call_info = active_calls.pop(call_id)
                processing_calls.add(call_id)
                if call_info["admin_msg_id"]: delete_message(config.ADMIN_CHAT_ID, call_info["admin_msg_id"])
                import threading
                threading.Thread(target=process_completed_call, args=(driver, call_info, call_id)).start()
    except: pass

def process_completed_call(driver, call_info, call_uuid):
    """Download and notify"""
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_path = os.path.join(DOWNLOAD_FOLDER, f"call_{call_info['did_number']}_{timestamp}.mp3")
        
        if download_voice_recording(driver, call_info, call_uuid, file_path):
            send_to_group_with_voice(call_info, file_path)
        else:
            send_download_failed_to_group(call_info)
    finally:
        if call_uuid in processing_calls: processing_calls.remove(call_uuid)

def download_voice_recording(driver, call_info, call_uuid, file_path):
    """Voice download engine"""
    try:
        driver.execute_script(f'window.Play("{call_info["did_number"]}", "{call_uuid}");')
        time.sleep(5)
        session = requests.Session()
        for cookie in driver.get_cookies(): session.cookies.set(cookie['name'], cookie['value'])
        response = session.get(call_info['full_url'], timeout=30)
        if response.status_code == 200 and len(response.content) > 1000:
            with open(file_path, 'wb') as f: f.write(res.content)
            return True
        return False
    except: return False

def send_to_group_with_voice(call_info, file_path):
    """Send formatted notification"""
    try:
        call_time = call_info['detected_at'].strftime('%Y-%m-%d %I:%M:%S %p')
        num = call_info['did_number']
        masked = num[:4] + "****" + num[-3:] if len(num) >= 8 else num[:4] + "****"
        caption = f"📳 New Call Captured!\n\n└ ⏰ Time: {call_time}\n└ {call_info['flag']} {call_info['country']}\n└ 📞 Number: {masked}\n"
        if send_voice_to_group(file_path, caption):
            if os.path.exists(file_path): os.remove(file_path)
    except: pass

def send_download_failed_to_group(call_info):
    """Notify failure"""
    try:
        num = call_info['did_number']
        masked = num[:4] + "****" + num[-3:]
        text = f"😟 Please contact admin\n\n└ {call_info['flag']} {call_info['country']}\n└ 📞 Number: {masked}\n└ ❌ Failed"
        send_message_to_group(text)
    except: pass

def check_login_status(driver):
    """Verify session"""
    return "login" not in driver.current_url

def refresh_with_cookies(driver):
    """Smart refresh"""
    try:
        driver.refresh()
        time.sleep(5)
        return check_login_status(driver)
    except: return False

def main():
    print("[🚀] Starting Orange Carrier Monitor...")
    driver = setup_chrome_driver_with_cookies()
    if not login_with_cookies(driver):
        print("[❌] Login failed"); return

    last_refresh = datetime.now()
    next_interval = get_next_refresh_time()
    
    while True:
        try:
            if (datetime.now() - last_refresh).total_seconds() > next_interval:
                if refresh_with_cookies(driver):
                    last_refresh = datetime.now()
                    next_interval = get_next_refresh_time()
            
            extract_calls(driver)
            time.sleep(config.CHECK_INTERVAL)
        except KeyboardInterrupt: break
        except Exception as e: print(f"[❌] Error: {e}"); time.sleep(5)
    
    if driver: driver.quit()

if __name__ == "__main__":
    main()
