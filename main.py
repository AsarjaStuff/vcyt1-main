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

# Function to detect Chrome binary path
def find_chrome_binary():
    possible_paths = [
        '/usr/bin/google-chrome-stable',  # Common path in Docker/Render
        '/opt/google/chrome/stable',  # Another possible path
        '/usr/bin/chromium',  # If you're using Chromium instead
        '/usr/local/bin/google-chrome-stable',  # Another possible location
    ]
    for path in possible_paths:
        if shutil.which(path):  # Check if the binary exists in the path
            return path
    return None  # Return None if no path is found

# Get environment variables
usertoken = os.getenv("TOKEN")
GUILD_ID = os.getenv("GUILD_ID")

if not usertoken or not GUILD_ID:
    print("[ERROR] Please add a token and guild ID inside the environment variables.")
    sys.exit()

# Validate the token
headers = {"Authorization": usertoken}
validate = requests.get('https://discord.com/api/v10/users/@me', headers=headers)
if validate.status_code != 200:
    print("[ERROR] Invalid token. Please check it again.")
    sys.exit()

# Set up WebDriver options
chrome_options = Options()
chrome_options.add_argument("--headless")  # Runs browser in background without opening a window
chrome_options.add_argument("--disable-gpu")  # Disable GPU acceleration
chrome_options.add_argument("--no-sandbox")  # Necessary for some environments, including Render
chrome_options.add_argument("--disable-dev-shm-usage")  # Necessary for Docker and cloud environments

# Automatically detect Chrome binary path
chrome_bin = find_chrome_binary()
if not chrome_bin:
    print("[ERROR] Chrome binary not found.")
    sys.exit()
chrome_options.binary_location = chrome_bin

# Initialize WebDriver
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

# Log into Discord using the provided token
driver.get("https://discord.com/login")
WebDriverWait(driver, 10).until(
    EC.presence_of_element_located((By.NAME, "email"))
)

# Enter the token using JavaScript execution
driver.execute_script(f"localStorage.setItem('token', '{usertoken}')")
driver.refresh()

# Wait for login to complete and the sidebar to be visible
WebDriverWait(driver, 10).until(
    EC.presence_of_element_located((By.CLASS_NAME, "guilds"))
)

# Navigate to the guild settings
driver.get(f"https://discord.com/channels/{GUILD_ID}/{GUILD_ID}")  # Adjust this URL to access the specific guild's server settings

# Wait for the page to load
WebDriverWait(driver, 10).until(
    EC.presence_of_element_located((By.CLASS_NAME, "guild-header"))
)

# Define the main loop to randomize and save
while True:
    try:
        # Access the settings by clicking the server settings button
        settings_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[@aria-label='Server Settings']"))
        )
        settings_button.click()

        # Wait for the guild settings to load
        guild_settings_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//div[@aria-label='Guild Settings']"))
        )
        guild_settings_button.click()

        # Wait for the "Guild Badge" section to be available and clickable
        guild_badge_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[text()='Guild Badge']"))
        )
        guild_badge_button.click()

        # Wait for the "Randomize" button to be visible and clickable
        randomize_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.NAME, "randomize"))  # Update if needed
        )

        # Click the "Randomize" button
        randomize_button.click()
        print("Randomize button clicked successfully!")

        # Wait for a save button and save changes (if present)
        save_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[text()='Save Changes']"))  # Update if needed
        )
        save_button.click()
        print("Changes saved successfully!")

        # Wait a bit before repeating the process
        time.sleep(10)

    except (NoSuchElementException, TimeoutException) as e:
        print(f"Error: {e} - Element not found or timeout occurred.")
        break
    except Exception as e:
        print(f"Unexpected error occurred: {e}")
        break

# Close the driver when done
driver.quit()
