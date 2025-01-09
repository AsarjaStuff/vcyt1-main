import os
import sys
import json
import time
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager

# Get environment variables
usertoken = os.getenv("TOKEN")
GUILD_ID = os.getenv("GUILD_ID")

if not usertoken or not GUILD_ID:
    print("[ERROR] Please add a token and guild ID inside the environment variables.")
    sys.exit()

# Validate the token using Discord API
headers = {"Authorization": usertoken, "Content-Type": "application/json"}
validate = requests.get("https://discord.com/api/v9/users/@me", headers=headers)
if validate.status_code != 200:
    print("[ERROR] Your token might be invalid. Please check it again.")
    sys.exit()

userinfo = validate.json()
username = userinfo["username"]
discriminator = userinfo["discriminator"]
userid = userinfo["id"]

# Print user information
print(f"Logged in as {username}#{discriminator} ({userid}).")

# Set up WebDriver options
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")

# Initialize WebDriver using webdriver-manager
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

try:
    # Log into Discord using the token
    driver.get("https://discord.com/login")
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "email")))
    driver.execute_script(f"localStorage.setItem('token', '{usertoken}')")
    driver.refresh()
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "guilds")))

    # Print success message
    print("Login successful! Automating badge customization...")

    while True:
        try:
            # Open server settings
            driver.get(f"https://discord.com/channels/{GUILD_ID}/{GUILD_ID}")
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "guild-header")))

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
                EC.element_to_be_clickable((By.NAME, "randomize"))  # Adjust as needed
            )
            randomize_button.click()
            print("Randomized badge successfully!")

            save_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[text()='Save Changes']"))
            )
            save_button.click()
            print("Saved changes successfully!")
            time.sleep(10)
        except (NoSuchElementException, TimeoutException) as e:
            print(f"Error: {e} - Element not found or timeout occurred.")
            break
except (TimeoutException, WebDriverException) as e:
    print(f"[ERROR] Failed to log in: {e}")
finally:
    driver.quit()
