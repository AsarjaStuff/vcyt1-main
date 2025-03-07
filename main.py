import os
import sys
import time
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, TimeoutException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager

# Fetch and validate environment variables
usertoken = os.getenv("TOKEN")
GUILD_ID = os.getenv("GUILD_ID")
CHROME_BIN = os.getenv("CHROME_BIN", "/usr/bin/google-chrome-stable")

# Sauce Labs credentials and tunnel
sauce_username = os.getenv('SAUCE_USERNAME', 'oauth-kasanwidjojojeiel-30890')
sauce_access_key = os.getenv('SAUCE_ACCESS_KEY', 'da6c39f1-bc81-4e03-ba16-b617ff0cc79f')
tunnel_name = 'oauth-kasanwidjojojeiel-30890_tunnel_name'

# Check for required environment variables
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
chrome_options = ChromeOptions()
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.binary_location = CHROME_BIN

# Sauce Labs capabilities with tunnel
sauce_options = {
    'username': sauce_username,
    'accessKey': sauce_access_key,
    'tunnelIdentifier': tunnel_name,
    'build': 'selenium-build-2TRBC',
    'name': 'Discord Automation Test',
    'extendedDebugging': True
}
chrome_options.set_capability('sauce:options', sauce_options)

# Use Sauce Labs tunnel with WebDriver for remote execution
driver = None  # Initialize outside loop to avoid NameError
retries = 3

for attempt in range(retries):
    try:
        # Remote WebDriver for Sauce Labs with Tunnel
        remote_url = "https://ondemand.eu-central-1.saucelabs.com:443/wd/hub"
        driver = webdriver.Remote(command_executor=remote_url, options=chrome_options)
        print("[DEBUG] WebDriver initialized with Sauce Labs using Sauce Connect.")

        # Log into Discord using token
        driver.get("https://discord.com/login")
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "email")))

        # Inject token, simulate refresh, and ensure login is successful
        driver.execute_script(f"localStorage.setItem('token', '{usertoken}')")
        driver.execute_script("window.location.reload();")  # Refresh after token injection

        WebDriverWait(driver, 15).until(EC.url_contains("discord.com/channels"))
        print("[DEBUG] Successfully logged in using token.")

        driver.get(f"https://discord.com/channels/{GUILD_ID}/{GUILD_ID}")
        print(f"[DEBUG] Navigated to guild page: {GUILD_ID}")

        # Simulate an interaction with the page
        while True:
            try:
                settings_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//*[@id='app-mount']/div[2]/div[1]/div[1]/div/div[2]/div/div/div/div/div[1]/nav/div[1]/header"))
                )
                settings_button.click()

                guild_settings_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//*[@id='guild-header-popout-settings']"))
                )
                guild_settings_button.click()

                randomize_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//*[@id='app-mount']/div[2]/div[1]/div[4]/div/div[2]/div[2]/div[2]/div[1]/div[1]/button"))
                )
                randomize_button.click()

                save_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//*[@id='app-mount']/div[2]/div[1]/div[4]/div/div[2]/div[2]/div[2]/div[2]/div/div/div/div[2]/button[2]"))
                )
                save_button.click()

                time.sleep(10)
            except (NoSuchElementException, TimeoutException) as e:
                print(f"[ERROR] Element not found or timeout: {e}")
                break
            except Exception as e:
                print(f"[ERROR] Unexpected error: {e}")
                break
    except WebDriverException as e:
        print(f"[ERROR] WebDriverException encountered: {e}")
        if attempt < retries - 1:
            print("[INFO] Retrying after a delay...")
            time.sleep(60)
        else:
            print("[ERROR] Max retries reached. Exiting.")
    finally:
        if driver:
            print("[DEBUG] Quitting the WebDriver.")
            driver.quit()
