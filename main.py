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

# Function to find the Chrome binary
def find_chrome_binary():
    # Check multiple possible paths for the Chromium or Chrome binary
    possible_paths = [
        "/usr/bin/chromium",  # Chromium's default path
        "/usr/bin/google-chrome",  # Google Chrome's path
        "/usr/bin/chrome"  # Another common path for Chrome
    ]
    for path in possible_paths:
        if os.path.exists(path):
            return path
    return None

# Function to find the ChromeDriver path
def find_chromedriver():
    chromedriver_path = ChromeDriverManager().install()
    return chromedriver_path

# Fetch the user token and guild ID from environment variables
usertoken = os.getenv("TOKEN")
GUILD_ID = os.getenv("GUILD_ID")

if not usertoken or not GUILD_ID:
    print("[ERROR] Please add a token and guild ID inside the environment variables.")
    sys.exit()

# Validate the provided token with the Discord API
headers = {"Authorization": usertoken}
validate = requests.get('https://discord.com/api/v10/users/@me', headers=headers)
if validate.status_code != 200:
    print("[ERROR] Invalid token. Please check it again.")
    sys.exit()

# Set up Chrome options for headless mode
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--remote-debugging-port=9222")

# Find the Chrome binary and assign it to the options
chrome_bin = find_chrome_binary()
if not chrome_bin:
    print("[ERROR] Chrome binary not found.")
    sys.exit()
chrome_options.binary_location = chrome_bin

# Get the ChromeDriver path
chromedriver_path = find_chromedriver()

# Print out the paths being used for debugging
print(f"Using Chrome binary located at: {chrome_bin}")
print(f"Using ChromeDriver located at: {chromedriver_path}")

# Set up the WebDriver and start the browser session
driver = webdriver.Chrome(service=Service(chromedriver_path), options=chrome_options)

# Navigate to the Discord login page
driver.get("https://discord.com/login")
WebDriverWait(driver, 10).until(
    EC.presence_of_element_located((By.NAME, "email"))
)

# Set the token in localStorage and refresh the page to log in
driver.execute_script(f"localStorage.setItem('token', '{usertoken}')")
driver.refresh()

# Wait until the guilds section is loaded after logging in
WebDriverWait(driver, 10).until(
    EC.presence_of_element_located((By.CLASS_NAME, "guilds"))
)

# Navigate to the specified guild page
driver.get(f"https://discord.com/channels/{GUILD_ID}/{GUILD_ID}")

# Wait until the guild header is loaded
WebDriverWait(driver, 10).until(
    EC.presence_of_element_located((By.CLASS_NAME, "guild-header"))
)

# Start interacting with the Discord server settings
while True:
    try:
        # Click the "Server Settings" button
        settings_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[@aria-label='Server Settings']"))
        )
        settings_button.click()

        # Click the "Guild Settings" option
        guild_settings_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//div[@aria-label='Guild Settings']"))
        )
        guild_settings_button.click()

        # Click the "Guild Badge" button
        guild_badge_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[text()='Guild Badge']"))
        )
        guild_badge_button.click()

        # Click the "Randomize" button
        randomize_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.NAME, "randomize"))
        )
        randomize_button.click()
        print("Randomize button clicked successfully!")

        # Save the changes
        save_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[text()='Save Changes']"))
        )
        save_button.click()
        print("Changes saved successfully!")

        # Wait before repeating the process
        time.sleep(10)

    except (NoSuchElementException, TimeoutException) as e:
        print(f"Error: {e} - Element not found or timeout occurred.")
        break
    except Exception as e:
        print(f"Unexpected error occurred: {e}")
        break

# Close the browser when done
driver.quit()
