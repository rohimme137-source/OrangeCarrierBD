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
        "value": "fb.1.1769074369749.830098219139516878",
        "domain": ".orangecarrier.com",
        "path": "/"
    },
    {
        "name": "XSRF-TOKEN",
        "value": "eyJpdiI6Ik9FcGFNTWFScWxqbjFESHlhSlZhS0E9PSIsInZhbHVlIjoidzl5a0lNQkc5TDNpdnNJMFgrWDJQdGxOWVRpXC9DY2VpMEhVZXo1RUxYTFZVbjVXdUNlc2tSZWprQ1Z6SGp2TVhYa2t3ZjJvdWtSbFUydVJxRmFIZlE0V2lOQnl3SnNOanVjT21KZnVlelhTVGI5dUJEdTd1YVhOVnVKelJCTGpHIiwibWFjIjoiMDI0NzEwOTdmM2FiYTg2NWEyMGRiYjA5NjczYmFlMmRhNWIwMTFjZDQ2ZDNlZmM2MThmMjEzZGExMzZjYTE5NiJ9",
        "domain": "www.orangecarrier.com",
        "path": "/"
    },
    {
        "name": "orange_carrier_session",
        "value": "eyJpdiI6IlFZQUtPRUl0ZFZLaUZxVXhZblo4MkE9PSIsInZhbHVlIjoiOUpreG9xMDQ1N0Y4T0wyUHd0Tyt4eFIwV0ZmdmtHUXN5VGxnM28rR29HRGFiRW1VRGU1TTFHMWQ0Y2xwTzRpdnk3UTN4ZEMrM3ZxNks3MUU4Wm9uUGplbFk1T0JVVDFYb0tRWTA5c0xWbzljTm5tczBtSTlxdlhBdkpkemkrRFMiLCJtYWMiOiJhNTBlNjQ3NTg3M2RjNjkwMWE3YzVkNWQ5NGFlMzM4ZGIzOWY0YjQ5NjAwZTI4MDA5YWZiODcxNDM3MzRhY2U2In0%3D",
        "domain": "www.orangecarrier.com",
        "path": "/"
    }      # ... add all other cookies
    ]
    
    # Settings
    MAX_ERRORS = 10
    CHECK_INTERVAL = 5
