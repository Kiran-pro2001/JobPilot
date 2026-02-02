import os
import json
import time
import random
import platform
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import Select
from backend_parser import get_ai_answer, get_ai_select_choice
from logger import log

def run_linkedin_bot(email, password):
    log("🚀 LinkedIn Bot: Starting execution...")
    # 1. Load User Data (for search keywords)
    if not os.path.exists('user_data.json'):
        raise Exception("No user data found. Please upload resume first.")

    with open('user_data.json', 'r') as f:
        user_data = json.load(f)
    
    # Resolve resume path for upload
    resume_path = os.path.abspath("latest_resume.pdf")
    if not os.path.exists(resume_path):
        log("⚠️ Resume file not found. Upload logic will be skipped.")

    job_role = user_data.get('job_role', 'Software Engineer')
    # location = "Remote" # Optional: You can hardcode or extract this too

    log(f"🤖 LinkedIn Agent Initialized for: {email}")
    log(f"🎯 Target Role: {job_role}")

    # 2. Setup Chrome
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled") # Anti-detection
    
    # --- SERVER CONFIGURATION (Required for Hostinger/Linux) ---
    if platform.system() == "Linux":
        options.add_argument("--headless=new") # Must be headless on server
        options.add_argument("--no-sandbox") # Required for root user
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--remote-debugging-port=9222") # Fix for DevToolsActivePort error
        options.add_argument("--disable-setuid-sandbox")
        options.add_argument("--disable-software-rasterizer")
        options.add_argument("--window-size=1920,1080")
    # -----------------------------------------------------------

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    wait = WebDriverWait(driver, 60) # Increased wait for manual Captcha solving

    try:
        # 3. Login
        log("🔑 Logging in...")
        driver.get("https://www.linkedin.com/login")
        
        driver.find_element(By.ID, "username").send_keys(email)
        time.sleep(1)
        driver.find_element(By.ID, "password").send_keys(password)
        time.sleep(1)
        driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()

        # Wait for login to complete (check for navbar)
        log("⏳ Waiting for login... (Please solve Captcha manually if it appears)")
        wait.until(EC.presence_of_element_located((By.ID, "global-nav")))
        log("✅ Login Successful")

        # 4. Search Jobs (Filtered by Easy Apply & Date Posted)
        # f_AL=true turns on "Easy Apply" filter
        # f_TPR=r86400 filters by "Past 24 hours" (Use r604800 for Past Week)
        search_url = f"https://www.linkedin.com/jobs/search/?keywords={job_role}&f_AL=true&f_TPR=r86400"
        driver.get(search_url)
        log(f"🔎 Searching: {search_url}")
        time.sleep(3)

        # 5. Iterate through Job Cards
        # Note: Selectors change often. These are standard as of late 2024.
        job_cards = driver.find_elements(By.CSS_SELECTOR, ".job-card-container")
        
        if not job_cards:
            log("⚠️ No jobs found on page 1. Try broadening your search (remove 'Past 24h' filter).")
            return

        log(f"👀 Found {len(job_cards)} potential jobs on page 1")

        for i, card in enumerate(job_cards): # Removed limit to keep running
            # Check for Stop Signal
            if os.path.exists("stop_signal.txt"):
                log("🛑 Stop signal received. Halting bot...")
                break

            # Check Payment Limits
            current_count = user_data.get('application_count', 0)
            is_premium = user_data.get('is_premium', False)
            if not is_premium and current_count >= 3:
                raise Exception("PAYMENT_REQUIRED")

            try:
                log(f"   👉 Processing Job {i+1}...")
                card.click()
                time.sleep(2) # Wait for details to load

                # Click "Easy Apply" button
                # There might be multiple buttons, we look for the primary one in the details pane
                apply_btn = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "jobs-apply-button--top-card")))
                apply_btn.click()
                log("      Clicked Easy Apply")
                time.sleep(2)
                
                # 6. Handle the Application Modal (Multi-step Loop)
                max_steps = 5
                for step in range(max_steps):
                    # A. Resume Upload (Crucial Step)
                    if os.path.exists(resume_path):
                        file_inputs = driver.find_elements(By.CSS_SELECTOR, "input[type='file']")
                        for inp in file_inputs:
                            try:
                                inp.send_keys(resume_path)
                                log("      📂 Resume uploaded")
                            except:
                                pass

                    # B. AI Form Filling (Text Inputs)
                    text_inputs = driver.find_elements(By.CSS_SELECTOR, "input[type='text'], textarea, input[type='tel'], input[type='email'], input[type='number']")
                    for inp in text_inputs:
                        if inp.is_displayed() and not inp.get_attribute("value"):
                            try:
                                input_id = inp.get_attribute("id")
                                if input_id:
                                    labels = driver.find_elements(By.CSS_SELECTOR, f"label[for='{input_id}']")
                                    if labels:
                                        label_text = labels[0].text
                                        answer = get_ai_answer(label_text, user_data)
                                        if answer:
                                            inp.send_keys(answer)
                                            inp.send_keys(Keys.TAB) # Trigger validation
                                            time.sleep(0.5)
                                            
                                            # Check for validation error (aria-invalid="true")
                                            if inp.get_attribute("aria-invalid") == "true":
                                                error_msg = "Invalid format"
                                                try:
                                                    # Try to find the error message text (LinkedIn standard class)
                                                    parent = inp.find_element(By.XPATH, "./..")
                                                    err_elem = parent.find_element(By.CSS_SELECTOR, ".artdeco-inline-feedback__message")
                                                    error_msg = err_elem.text
                                                except:
                                                    pass
                                                
                                                log(f"      ⚠️ Validation Error: '{error_msg}'. Retrying with AI...")
                                                corrected = get_ai_answer(label_text, user_data, error_message=error_msg)
                                                if corrected:
                                                    inp.clear()
                                                    inp.send_keys(corrected)
                                                    inp.send_keys(Keys.TAB)
                                                    time.sleep(0.5)
                            except:
                                pass

                    # C. AI Form Filling (Select/Dropdowns)
                    select_inputs = driver.find_elements(By.TAG_NAME, "select")
                    for select in select_inputs:
                        if select.is_displayed():
                            try:
                                input_id = select.get_attribute("id")
                                if input_id:
                                    labels = driver.find_elements(By.CSS_SELECTOR, f"label[for='{input_id}']")
                                    if labels:
                                        label_text = labels[0].text
                                        
                                        # Get options
                                        sel_obj = Select(select)
                                        options = [opt.text for opt in sel_obj.options if opt.text.strip()]
                                        
                                        if options:
                                            choice = get_ai_select_choice(label_text, options, user_data)
                                            if choice:
                                                try:
                                                    sel_obj.select_by_visible_text(choice)
                                                except:
                                                    # Fuzzy match fallback
                                                    for opt in options:
                                                        if choice.lower() in opt.lower():
                                                            sel_obj.select_by_visible_text(opt)
                                                            break
                                            time.sleep(0.5)
                            except:
                                pass

                    # D. AI Form Filling (Radio Buttons)
                    fieldsets = driver.find_elements(By.TAG_NAME, "fieldset")
                    for fieldset in fieldsets:
                        try:
                            # Check if any radio in this fieldset is already selected
                            radios = fieldset.find_elements(By.CSS_SELECTOR, "input[type='radio']")
                            if any(r.is_selected() for r in radios):
                                continue # Already answered

                            legend = fieldset.find_element(By.TAG_NAME, "legend").text
                            
                            # Get labels for radios and map text to the clickable element
                            options_map = {}
                            labels = fieldset.find_elements(By.TAG_NAME, "label")
                            for label in labels:
                                text = label.text.strip()
                                if text:
                                    options_map[text] = label
                            
                            if options_map:
                                options = list(options_map.keys())
                                choice = get_ai_select_choice(legend, options, user_data)
                                if choice in options_map:
                                    # Use JS click for reliability on custom radio UIs
                                    driver.execute_script("arguments[0].click();", options_map[choice])
                                    time.sleep(0.5)
                        except:
                            pass

                    # E. AI Form Filling (Checkboxes)
                    checkboxes = driver.find_elements(By.CSS_SELECTOR, "input[type='checkbox']")
                    for cb in checkboxes:
                        if cb.is_displayed() and not cb.is_selected():
                            try:
                                input_id = cb.get_attribute("id")
                                if input_id:
                                    labels = driver.find_elements(By.CSS_SELECTOR, f"label[for='{input_id}']")
                                    if labels:
                                        label_text = labels[0].text
                                        # Ask AI if we should check it (Defaulting to Yes/True for completion)
                                        answer = get_ai_answer(f"Should I check the box for: '{label_text}'? Answer Yes or No.", user_data)
                                        
                                        if "yes" in answer.lower():
                                            driver.execute_script("arguments[0].click();", cb)
                                            time.sleep(0.5)
                            except:
                                pass

                    # F. Check for Submit Button
                    submit_btn = driver.find_elements(By.CSS_SELECTOR, "button[aria-label='Submit application']")
                    if submit_btn:
                        log("      🚀 Submit button found! Applying...")
                        # Use JS click for submit as well
                        driver.execute_script("arguments[0].click();", submit_btn[0])
                        time.sleep(3)
                        # Close Success Modal
                        close_btn = driver.find_elements(By.CSS_SELECTOR, "button[aria-label='Dismiss']")
                        if close_btn: 
                            driver.execute_script("arguments[0].click();", close_btn[0])
                        log("      ✅ Application Sent!")
                        break
                    
                    # Increment Application Count
                    user_data['application_count'] = user_data.get('application_count', 0) + 1
                    with open('user_data.json', 'w') as f:
                        json.dump(user_data, f, indent=4)
                    
                    # G. Check for Next/Review Button
                    next_btn = driver.find_elements(By.CSS_SELECTOR, "button[aria-label='Continue to next step']")
                    if not next_btn:
                        next_btn = driver.find_elements(By.CSS_SELECTOR, "button[aria-label='Review your application']")
                    
                    if next_btn:
                        # Use JS click for next
                        driver.execute_script("arguments[0].click();", next_btn[0])
                        time.sleep(2)
                    else:
                        # Stuck or unknown state
                        break

            except Exception as e:
                log(f"      ❌ Could not apply to this job: {str(e)[:50]}")
                continue
            
            # Human-like delay between jobs (5 to 10 seconds)
            delay = random.uniform(5, 10)
            log(f"⏳ Waiting {delay:.1f}s before next job to avoid detection...")
            time.sleep(delay)
        
        log("🏁 Batch complete.")
        
        # Save a log for the history page
        from apply_bot import save_history
        save_history({
            "company": "LinkedIn Network",
            "role": job_role,
            "status": "Batch Processed",
            "date": time.strftime("%Y-%m-%d %H:%M:%S")
        })

    except Exception as e:
        log(f"❌ Bot Error: {e}")
        raise e
    finally:
        log("🛑 Closing Driver...")
        driver.quit()