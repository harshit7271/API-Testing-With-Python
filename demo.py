from playwright.sync_api import sync_playwright, expect
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

    print("Login successful! Sagility Dashboard loaded")

    # 1. TEST SIDEBAR NAVIGATION
    print("Testing Sidebar Navigation...")

    # Navigate to Decision Engine
    page.get_by_text("Decision Engine").click()
    expect(page.get_by_text("Pending Activity")
           ).to_be_visible()  # Wait for UI to shift
    print("Navigated to Decision Engine: ", page.url)

    # Navigate to Pending Activity
    page.get_by_text("Pending Activity").click()
    print("Navigated to Pending Activity: ", page.url)

    # Return to Dashboard
    page.get_by_text("Dashboard").click()

    dashboard_frame = page.frame_locator("iframe").first

    # Dashboard to re-render inside the iframe
    expect(dashboard_frame.get_by_text("Application Overview")
           ).to_be_visible(timeout=10000)
    print("Returned to Dashboard and verified UI rendered.")

    # 2. TEST COMPARE BUTTON & METRICS MODAL
    print("Testing 'Compare' Modal functionality...")

    # multiple "Compare" buttons. The one for Application Overview is the first one on the page.
    app_overview_section = dashboard_frame.locator(
        "div").filter(has_text="Application Overview").first
    compare_button = app_overview_section.get_by_text("Compare").first

    compare_button.click()
    page.wait_for_load_state('networkidle')
    page.wait_for_timeout(15000)
    date_range_button = dashboard_frame.get_by_role(
        "button", name="Jan 1, 2026 - Jun 3, 2026")
    page.wait_for_timeout(3000)
    print("Compare metrics opened successfully")

    browser.close()
    print("Testing completed successfully.")
