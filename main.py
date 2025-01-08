import os
import sys
import json
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from keep_alive import keep_alive

# Set up status for the bot (optional)
status = "online"  # online/dnd/idle

# Set up WebDriver options
chrome_options = Options()
chrome_options.add_argument("--headless")  # Runs browser in background without opening a window
chrome_options.add_argument("--disable-gpu")  # Disable GPU acceleration (optional)
chrome_options.add_argument("--no-sandbox")  # Needed for some environments, including Render
chrome_options.add_argument("--disable-dev-shm-usage")  # Required for Docker and cloud environments

# Path to your chromedriver in the Render environment
chromedriver_path = "/usr/bin/chromedriver"  # This should be the default location for Render's chromedriver

# Check if chromedriver exists (for debugging purposes)
if not os.path.exists(chromedriver_path):
    print("[ERROR] Chromedriver not found at the specified path.")
    sys.exit()

# Start the WebDriver
driver = webdriver.Chrome(service=Service(chromedriver_path), options=chrome_options)

usertoken = os.getenv("TOKEN")
if not usertoken:
    print("[ERROR] Please add a token inside Secrets.")
    sys.exit()

headers = {"Authorization": usertoken, "Content-Type": "application/json"}

# Validate token
validate = requests.get('https://canary.discordapp.com/api/v9/users/@me', headers=headers)
if validate.status_code != 200:
    print("[ERROR] Your token might be invalid. Please check it again.")
    sys.exit()

# Fetch user info
userinfo = requests.get('https://canary.discordapp.com/api/v9/users/@me', headers=headers).json()
username = userinfo["username"]
discriminator = userinfo["discriminator"]
userid = userinfo["id"]

print(f"Logged in as {username}#{discriminator} ({userid}).")

# Open the specified Discord channel URL in the browser
discord_channel_url = "https://discord.com/channels/1212249546948870185/1285260197874630696"
driver.get(discord_channel_url)

# Wait for the page to load and make sure we're logged in
WebDriverWait(driver, 10).until(
    EC.presence_of_element_located((By.CLASS_NAME, "guilds"))  # Wait until the sidebar is visible
)

# Loop for performing the "randomize" action in the server settings
while True:
    try:
        # Navigate to server settings by clicking the settings icon
        settings_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//button[@aria-label="Server Settings"]'))  # Update XPath if needed
        )
        settings_button.click()

        # Wait for the Guild Settings to load
        guild_settings_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//div[@aria-label="Guild Settings"]'))  # Update XPath
        )
        guild_settings_button.click()

        # Wait for the Guild Badge settings to be visible
        guild_badge_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//button[text()="Guild Badge"]'))  # Update XPath
        )
        guild_badge_button.click()

        # Wait for the "Randomize" button to become clickable
        randomize_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.NAME, "randomize"))  # Update if necessary
        )

        # Click "Randomize"
        randomize_button.click()
        print("Randomize button clicked successfully!")

        # Save changes (if there's a save button, you would click it here)
        save_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//button[text()="Save Changes"]'))  # Update XPath if needed
        )
        save_button.click()
        print("Changes saved successfully!")

        # Wait for a bit before repeating
        WebDriverWait(driver, 10).until(
            EC.staleness_of(randomize_button)  # Ensure the button becomes stale before proceeding
        )
    except (NoSuchElementException, TimeoutException) as e:
        print(f"Error: {e} - Element not found or timeout occurred.")
        break
    except Exception as e:
        print(f"Error occurred: {e}")
        break

# Start the Flask server in the background
keep_alive()

# Your bot's logic (run the joiner function or similar)
run_joiner()
