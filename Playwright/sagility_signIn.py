from playwright.sync_api import sync_playwright
from dotenv import load_dotenv
import os

load_dotenv()

EMAIL = os.getenv('EMAIL')
PASSWORD = os.getenv('PASSWORD')

if EMAIL is None or PASSWORD is None:
    raise ValueError('EMAIL and PASSWORD environment variables must be set')

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()
    page.goto("https://hire-admin-qa.bling-ai.com/portal/index.html")
    print("Page title:", page.title())

    # Wait for page to fully load
    page.wait_for_load_state('networkidle')

    page.get_by_placeholder("Enter your email").fill(EMAIL)
    page.get_by_placeholder("Enter your password").fill(PASSWORD)

    page.screenshot(path='signin-page.png')

    # Click the Sign In button
    page.click('button[type="submit"]')
    print("Login successful, welcome message found.")

    # Wait for page to navigate after login
    page.wait_for_load_state('networkidle')
    page.wait_for_timeout(8000)  # Wait 8 seconds for content to load

    # we'll print what changed after login
    print("After login - Page title:", page.title())
    print("After login - URL:", page.url)

    # Take screenshot to verify
    page.screenshot(path='after-login.png')

    print("Login successful!")

    browser.close()
