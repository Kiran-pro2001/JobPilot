import os
import json
import time
import traceback
import platform
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from logger import log

def save_history(entry):
    history_file = 'application_history.json'
    history = []
    
    if os.path.exists(history_file):
        try:
            with open(history_file, 'r') as f:
                history = json.load(f)
        except json.JSONDecodeError:
            history = []
    
    history.insert(0, entry) # Add new entry to the top
    with open(history_file, 'w') as f:
        json.dump(history, f, indent=4)

def run_application_bot():
    log("🚀 Auto-Apply Bot: Starting execution...")
    # 1. Load User Data
    if not os.path.exists('user_data.json'):
        log("❌ No user data found. Please upload a resume first via the UI.")
        return

    with open('user_data.json', 'r') as f:
        user_data = json.load(f)

    resume_path = os.path.abspath("latest_resume.pdf")
    if not os.path.exists(resume_path):
        log("❌ Resume file not found.")
        return

    log("🤖 Bot initializing...")
    log(f"   Candidate: {user_data.get('name')}")
    log(f"   Target: TechCorp Demo Portal")

    # 2. Setup Selenium (Chrome)
    options = webdriver.ChromeOptions()
    
    # Robust check for Production/Server environment
    is_production = os.environ.get("RENDER") or os.path.exists("/.dockerenv") or platform.system() == "Linux"
    log(f"🔍 Debug: Environment Check -> RENDER: {os.environ.get('RENDER')}, Docker: {os.path.exists('/.dockerenv')}, OS: {platform.system()}")

    if is_production:
        log("⚙️ Configuring Chrome for Production (Headless)...")
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-software-rasterizer")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--disable-notifications")
        options.add_argument("--disable-setuid-sandbox")
        options.add_argument("--remote-debugging-port=9222") # Fix for DevToolsActivePort error
    else:
        log("⚙️ Configuring Chrome for Local (Headless)...")
        options.add_argument("--headless=new") # Local headless

    try:
        log("🔧 Initializing WebDriver...")
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        log("✅ WebDriver initialized successfully.")
    except Exception as e:
        log(f"❌ WebDriver Initialization Failed: {e}")
        raise e

    try:
        # 3. Open the Demo Page
        # We use the absolute path to the local HTML file
        file_path = os.path.abspath("apply_demo.html")
        driver.get(f"file://{file_path}")
        
        time.sleep(1) # Wait for load

        # 4. Fill the Form
        log("📝 Filling application form...")
        
        # Name
        driver.find_element(By.ID, "fullname").send_keys(user_data.get('name', ''))
        
        # Email
        driver.find_element(By.ID, "email").send_keys(user_data.get('email', ''))
        
        # Phone
        driver.find_element(By.ID, "phone").send_keys(user_data.get('phone', ''))
        
        # Cover Letter (Using the summary from AI)
        driver.find_element(By.ID, "cover_letter").send_keys(user_data.get('summary', ''))
        
        # File Upload
        driver.find_element(By.ID, "resume").send_keys(resume_path)
        
        time.sleep(2) # Pause so you can see it happening

        # 5. Submit
        log("🚀 Submitting application...")
        driver.find_element(By.TAG_NAME, "button").click()
        
        time.sleep(3) # Wait to see success message
        log("✅ Application successful!")

        # Capture Screenshot
        screenshot_path = "application_success.png"
        driver.save_screenshot(screenshot_path)
        log(f"📸 Screenshot saved to: {os.path.abspath(screenshot_path)}")

        # Log to History
        history_entry = {
            "company": "TechCorp",
            "role": "Senior Engineer",
            "status": "Applied",
            "date": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        save_history(history_entry)

        # Bot finished

    except Exception as e:
        log(f"\n❌ An error occurred: {e}")
        traceback.print_exc()

    finally:
        driver.quit()

if __name__ == "__main__":
    run_application_bot()