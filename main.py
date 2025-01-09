import os
import sys
import time
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from webdriver_manager.chrome import ChromeDriverManager  # Import webdriver-manager

# Fetch and validate environment variables
usertoken = os.getenv("TOKEN")
GUILD_ID = os.getenv("GUILD_ID")
CHROME_BIN = os.getenv("CHROME_BIN", "/usr/bin/chromium")

print("[DEBUG] Starting the script...")

if not usertoken or not GUILD_ID:
    print("[ERROR] Missing TOKEN or GUILD_ID in environment variables.")
    sys.exit()

# Validate token
headers = {"Authorization": usertoken}
response = requests.get('https://discord.com/api/v10/users/@me', headers=headers)
print(f"[DEBUG] Token validation response: {response.status_code} - {response.text}")
if response.status_code != 200:
    print(f"[ERROR] Invalid token: {response.status_code} - {response.text}")
    sys.exit()

# Set up Chrome options
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.binary_location = CHROME_BIN

# Print paths for debugging
print(f"[DEBUG] Using Chrome binary located at: {CHROME_BIN}")

# Initialize WebDriver using webdriver-manager to automatically get the right version of chromedriver
try:
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    print("[DEBUG] WebDriver initialized successfully.")
except Exception as e:
    print(f"[ERROR] Failed to initialize WebDriver: {e}")
    sys.exit()

try:
    # Log into Discord using token
    driver.get("https://discord.com/login")
    print("[DEBUG] Navigated to Discord login page.")
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "email")))

    # Inject token into localStorage
    driver.execute_script(f"localStorage.setItem('token', '{usertoken}')")
    driver.refresh()
    print("[DEBUG] Token set in localStorage and page refreshed.")

    # Navigate to the specified guild
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "guilds")))

    driver.get(f"https://discord.com/channels/{GUILD_ID}/{GUILD_ID}")
    print(f"[DEBUG] Navigated to guild page: {GUILD_ID}")
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "guild-header")))

    while True:
        try:
            # Click Server Settings
            settings_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[@aria-label='Server Settings']"))
            )
            settings_button.click()
            print("[DEBUG] Server Settings button clicked.")

            # Click Guild Settings
            guild_settings_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//div[@aria-label='Guild Settings']"))
            )
            guild_settings_button.click()
            print("[DEBUG] Guild Settings button clicked.")

            # Click Guild Badge and Randomize
            guild_badge_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[text()='Guild Badge']"))
            )
            guild_badge_button.click()
            print("[DEBUG] Guild Badge button clicked.")

            randomize_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.NAME, "randomize"))
            )
            randomize_button.click()
            print("[DEBUG] Randomize button clicked successfully.")

            # Save changes
            save_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[text()='Save Changes']"))
            )
            save_button.click()
            print("[DEBUG] Changes saved successfully.")

            time.sleep(10)

        except (NoSuchElementException, TimeoutException) as e:
            print(f"[ERROR] Element not found or timeout: {e}")
            break
        except Exception as e:
            print(f"[ERROR] Unexpected error: {e}")
            break

finally:
    print("[DEBUG] Quitting the WebDriver.")
    driver.quit()
