import time
import re
import requests
import os
import random
import json
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
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
    def mock_open(*args, **kwargs): raise NotImplementedError("aifc removed")
    m.open = mock_open
    sys.modules["aifc"] = m

active_calls = {}
processing_calls = set()
refresh_pattern_index = 0
REFRESH_PATTERN = [1800, 1545, 2110, 1850, 1340]

DOWNLOAD_FOLDER = './downloads'
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

def get_next_refresh_time():
    global refresh_pattern_index
    interval = REFRESH_PATTERN[refresh_pattern_index]
    refresh_pattern_index = (refresh_pattern_index + 1) % len(REFRESH_PATTERN)
    print(f"[🔄] Next refresh in {interval}s")
    return interval

def detect_country(number):
    try:
        clean_number = re.sub(r"\D", "", number)
        parsed = phonenumbers.parse("+" + clean_number, None)
        region = region_code_for_number(parsed)
        country = pycountry.countries.get(alpha_2=region)
        flag = "".join(chr(127397 + ord(c)) for c in region.upper())
        return country.name, flag
    except: return "Unknown", "🏳️"

def send_message_to_admin(text):
    try:
        url = f"https://api.telegram.org/bot{config.BOT_TOKEN}/sendMessage"
        res = requests.post(url, json={"chat_id": config.ADMIN_CHAT_ID, "text": text, "parse_mode": "Markdown"})
        return res.json().get("result", {}).get("message_id") if res.ok else None
    except: return None

def send_voice_to_group(voice_path, caption):
    try:
        url = f"https://api.telegram.org/bot{config.BOT_TOKEN}/sendVoice"
        with open(voice_path, "rb") as voice:
            res = requests.post(url, data={"chat_id": config.GROUP_CHAT_ID, "caption": caption, "parse_mode": "HTML"}, files={"voice": voice})
            return res.status_code == 200
    except: return False

def setup_chrome_driver_with_cookies():
    """Optimized for Selenium 4.9.1 in Termux"""
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    
    # টারমাক্স স্পেসিফিক পাথ
    chrome_options.binary_location = "/data/data/com.termux/files/usr/bin/chromium"
    termux_driver_path = "/data/data/com.termux/files/usr/bin/chromedriver"

    print(f"[🔧] Starting with Selenium 4.9.1... Path: {termux_driver_path}")
    
    try:
        # পদ্ধতি ১: সরাসরি পাথ ব্যবহার (Selenium 4.9.1 এর জন্য আদর্শ)
        driver = webdriver.Chrome(
            executable_path=termux_driver_path, 
            options=chrome_options
        )
    except:
        # পদ্ধতি ২: সার্ভিস অবজেক্ট ব্যবহার
        service = Service(termux_driver_path)
        driver = webdriver.Chrome(service=service, options=chrome_options)

    try:
        driver.get("https://www.orangecarrier.com")
        time.sleep(2)
        driver.delete_all_cookies()
        for cookie in config.ORANGE_COOKIES:
            c = cookie.copy()
            if 'expirationDate' in c: c['expiry'] = int(c['expirationDate'])
            for key in ['hostOnly', 'storeId', 'sameSite', 'expirationDate']:
                c.pop(key, None)
            driver.add_cookie(c)
        driver.refresh()
        time.sleep(3)
        print("[✅] WebDriver & Cookies Loaded!")
    except Exception as ce:
        print(f"[⚠️] Cookie Error: {ce}")

    return driver

def extract_calls(driver):
    global active_calls, processing_calls
    try:
        table = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "LiveCalls")))
        rows = table.find_elements(By.TAG_NAME, "tr")
        current_ids = set()
        for row in rows:
            rid = row.get_attribute('id')
            if not rid: continue
            cells = row.find_elements(By.TAG_NAME, "td")
            if len(cells) < 2: continue
            num = re.sub(r"\D", "", cells[1].text)
            current_ids.add(rid)
            
            if rid not in active_calls:
                c_name, flag = detect_country(num)
                full_url = f"https://www.orangecarrier.com/live/calls/sound?did={num}&uuid={rid}"
                msg = send_message_to_admin(f"📞 {num}\n🔗 {full_url}")
                active_calls[rid] = {"admin_msg_id": msg, "flag": flag, "country": c_name, "num": num, "at": datetime.now(), "url": full_url}
        
        for cid in list(active_calls.keys()):
            if cid not in current_ids and cid not in processing_calls:
                info = active_calls.pop(cid)
                processing_calls.add(cid)
                if info["admin_msg_id"]:
                    requests.post(f"https://api.telegram.org/bot{config.BOT_TOKEN}/deleteMessage", data={"chat_id": config.ADMIN_CHAT_ID, "message_id": info["admin_msg_id"]})
                
                import threading
                threading.Thread(target=process_call, args=(driver, info, cid)).start()
    except: pass

def process_call(driver, info, cid):
    try:
        path = os.path.join(DOWNLOAD_FOLDER, f"{info['num']}_{cid}.mp3")
        driver.execute_script(f'window.Play("{info["num"]}", "{cid}");')
        time.sleep(5)
        
        session = requests.Session()
        for ck in driver.get_cookies(): session.cookies.set(ck['name'], ck['value'])
        res = session.get(info['url'], stream=True)
        
        if res.status_code == 200:
            with open(path, 'wb') as f: f.write(res.content)
            masked = info['num'][:4] + "****" + info['num'][-3:]
            cap = f"📳 New Call Captured!\n\n└ ⏰ Time: {info['at'].strftime('%I:%M:%S %p')}\n└ {info['flag']} {info['country']}\n└ 📞 Number: {masked}"
            send_voice_to_group(path, cap)
            if os.path.exists(path): os.remove(path)
    finally:
        if cid in processing_calls: processing_calls.remove(cid)

def main():
    driver = setup_chrome_driver_with_cookies()
    driver.get(config.CALL_URL)
    
    last_refresh = datetime.now()
    next_interval = get_next_refresh_time()
    
    while True:
        try:
            if (datetime.now() - last_refresh).total_seconds() > next_interval:
                driver.refresh()
                last_refresh = datetime.now()
                next_interval = get_next_refresh_time()
            
            extract_calls(driver)
            time.sleep(config.CHECK_INTERVAL)
        except KeyboardInterrupt: break
        except: time.sleep(5)
    driver.quit()

if __name__ == "__main__":
    main()
