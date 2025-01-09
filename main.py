import os
import sys
import time
import requests
import shutil
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
import subprocess

def find_chrome_binary():
    try:
        chrome_bin = subprocess.check_output(["/usr/bin/env", "google-chrome-stable"]).decode("utf-8").strip()
        return chrome_bin
    except subprocess.CalledProcessError:
        return None

def find_chromedriver():
    chromedriver_path = ChromeDriverManager().install()
    return chromedriver_path

usertoken = os.getenv("TOKEN")
GUILD_ID = os.getenv("GUILD_ID")

if not usertoken or not GUILD_ID:
    print("[ERROR] Please add a token and guild ID inside the environment variables.")
    sys.exit()

headers = {"Authorization": usertoken}
validate = requests.get('https://discord.com/api/v10/users/@me', headers=headers)
if validate.status_code != 200:
    print("[ERROR] Invalid token. Please check it again.")
    sys.exit()

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--remote-debugging-port=9222")

chrome_bin = find_chrome_binary()
if not chrome_bin:
    print("[ERROR] Chrome binary not found.")
    sys.exit()
chrome_options.binary_location = chrome_bin

chromedriver_path = find_chromedriver()

print(f"Using Chrome binary located at: {chrome_bin}")
print(f"Using ChromeDriver located at: {chromedriver_path}")

driver = webdriver.Chrome(service=Service(chromedriver_path), options=chrome_options)

driver.get("https://discord.com/login")
WebDriverWait(driver, 10).until(
    EC.presence_of_element_located((By.NAME, "email"))
)

driver.execute_script(f"localStorage.setItem('token', '{usertoken}')")
driver.refresh()

WebDriverWait(driver, 10).until(
    EC.presence_of_element_located((By.CLASS_NAME, "guilds"))
)

driver.get(f"https://discord.com/channels/{GUILD_ID}/{GUILD_ID}")

WebDriverWait(driver, 10).until(
    EC.presence_of_element_located((By.CLASS_NAME, "guild-header"))
)

while True:
    try:
        settings_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[@aria-label='Server Settings']"))
        )
        settings_button.click()

        guild_settings_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//div[@aria-label='Guild Settings']"))
        )
        guild_settings_button.click()

        guild_badge_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[text()='Guild Badge']"))
        )
        guild_badge_button.click()

        randomize_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.NAME, "randomize"))
        )

        randomize_button.click()
        print("Randomize button clicked successfully!")

        save_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[text()='Save Changes']"))
        )
        save_button.click()
        print("Changes saved successfully!")

        time.sleep(10)

    except (NoSuchElementException, TimeoutException) as e:
        print(f"Error: {e} - Element not found or timeout occurred.")
        break
    except Exception as e:
        print(f"Unexpected error occurred: {e}")
        break

driver.quit()
