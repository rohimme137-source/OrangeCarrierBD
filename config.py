import os
import json

# Heroku vs Local
IS_HEROKU = os.environ.get('DYNO') is not None

if IS_HEROKU:
    # Heroku config
    BOT_TOKEN = os.environ.get('BOT_TOKEN', '')
    ADMIN_CHAT_ID = os.environ.get('ADMIN_CHAT_ID', '')
    GROUP_CHAT_ID = os.environ.get('GROUP_CHAT_ID', '')
    
    # Orange Carrier Login Credentials (fallback)
    ORANGE_EMAIL = os.environ.get('ORANGE_EMAIL', '')
    ORANGE_PASSWORD = os.environ.get('ORANGE_PASSWORD', '')
    
    # URLs
    LOGIN_URL = os.environ.get('LOGIN_URL', 'https://www.orangecarrier.com/login')
    CALL_URL = os.environ.get('CALL_URL', 'https://www.orangecarrier.com/live/calls')
    BASE_URL = os.environ.get('BASE_URL', 'https://www.orangecarrier.com')
    
    # Cookies from environment variable (JSON string)
    cookies_env = os.environ.get('ORANGE_COOKIES', '')
    ORANGE_COOKIES = json.loads(cookies_env) if cookies_env else []
    
    # Settings
    MAX_ERRORS = int(os.environ.get('MAX_ERRORS', '10'))
    CHECK_INTERVAL = int(os.environ.get('CHECK_INTERVAL', '5'))
    
else:
    # Local development Configuration
    BOT_TOKEN = '8552186596:AAFZ6W1-t9P5gagS8DD-ecLh7lXLmzSsiPM'
    ADMIN_CHAT_ID = '8569268347'
    GROUP_CHAT_ID = '-1003843283210'
    
    # Orange Carrier Login Credentials
    ORANGE_EMAIL = 'rohimme137@gmail.com'
    ORANGE_PASSWORD = 'rohim0185'
    
    # URLs
    LOGIN_URL = 'https://www.orangecarrier.com/login'
    CALL_URL = 'https://www.orangecarrier.com/live/calls'
    BASE_URL = 'https://www.orangecarrier.com'
    
    # Cookies (paste your cookies here as Python list)
    ORANGE_COOKIES = [
     {
        "name": "_fbp",
        "value": "fb.1.1777985388145.660271859241425319",
        "domain": ".orangecarrier.com",
        "path": "/",
        "expirationDate": 1777985388,
    }
    {
        "domain": "www.orangecarrier.com",
        "expirationDate": 1777994891,
        "hostOnly": False,
        "httpOnly": False,
        "name": "XSRF-TOKEN",
        "path": "/",
        "sameSite": "unspecified",
        "secure": False,
        "session": False,
        "value": "eyJpdiI6Ik5idXZPVVQ1K1BPZnF2Q3FDamExa0E9PSIsInZhbHVlIjoiTE9WdFlvVERHTXZjN2lmNCtEMFl1Tk1zUEJ2dXVnTkRrbmtyYkJZV1Y1VkVpYTdDWEVLYUVnYXlJMUQyVHE2b1NaeXliTXBRTnJ4b0xTSGhqVVNjUFVzNjZWTlpLWDlDRUYwXC9MeXM2WEtFMVNkZjVOemE2K245WXVzYzR3cUVrIiwibWFjIjoiNzc5MjYzNTM5YmNjNmE2NDdiMGFmOWY3ZTM0NTNlNmM0ZDg2OTg5MTgwZjNjZDcxMTQ4NDk5MTk2YWY2OWE2NyJ9"
    },
    {
        "domain": "www.orangecarrier.com",
        "expirationDate": 1777994891,
        "hostOnly": False,
        "httpOnly": False,
        "name": "orange_carrier_session",
        "path": "/",
        "sameSite": "unspecified",
        "secure": False,
        "session": False,
        "value": "eyJpdiI6ImY1ZHR2T1wvaVdjUXlQdFVcL1ZEUjU2dz09IiwidmFsdWUiOiI5dWVKRXdUVEc1Yk54ZEk4Q0RRXC9pZkozbVppc3dqRG1Tc2YyNUF4ZHBMWlIzZW0rWlp3MklhZkcrQVFEVHQ3cHpIdnZYMmVjYTdwSVdjaFpDS1ZLMUl2ZkNXZytVS2FHbXRBbkYrMWRZMk03R2NSZk9pNVNXOGUzZ3NWY05pb3ciLCJtYWMiOiJlMzRkZTA1ZGRiMjg1YTNmOWRjNzg5ODQyMjk2ZThkNmUwZGFiMjg1NGRlZWQ4ZTBlZDEyNDc5MjdmNzdkZmUyIn0%3D"
    }
]

    
    # Settings
    MAX_ERRORS = 10
    CHECK_INTERVAL = 5
