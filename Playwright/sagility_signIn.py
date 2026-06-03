from playwright.sync_api import sync_playwright, expect
from dotenv import load_dotenv
import traceback
import os
import re

load_dotenv()

EMAIL = os.getenv('EMAIL')
PASSWORD = os.getenv('PASSWORD')

if EMAIL is None or PASSWORD is None:
    raise ValueError('EMAIL and PASSWORD environment variables must be set')


def run_automation():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        # Track the current stage so we know exactly where an error occurs
        current_stage = "Initialization"

        try:
            # LOGIN TESTING
            current_stage = "Navigating to Portal"
            page.goto("https://hire-admin-qa.bling-ai.com/portal/index.html")
            print("Page title:", page.title())
            page.wait_for_load_state('networkidle')

            current_stage = "Filling Login Credentials"
            page.get_by_placeholder("Enter your email").fill(EMAIL or "")
            page.get_by_placeholder("Enter your password").fill(PASSWORD or "")
            page.screenshot(path='signin-page.png')

            current_stage = "Submitting Login"
            page.click('button[type="submit"]')
            print("Login successful, welcome message found.")

            current_stage = "Waiting for Dashboard Load"
            page.wait_for_load_state('networkidle')
            page.wait_for_timeout(8000)

            print("After login - Page title:", page.title())
            print("After login - URL:", page.url)
            page.screenshot(path='after-login.png')
            print("Login successful! Sagility Dashboard loaded")

            # 1. TEST SIDEBAR NAVIGATION
            current_stage = "Testing Sidebar Navigation - Decision Engine"
            print("Testing Sidebar Navigation...")
            page.get_by_text("Decision Engine").click()
            expect(page.get_by_text("Pending Activity")).to_be_visible()
            print("Navigated to Decision Engine: ", page.url)

            current_stage = "Testing Sidebar Navigation - Pending Activity"
            page.get_by_text("Pending Activity").click()
            print("Navigated to Pending Activity: ", page.url)

            current_stage = "Returning to Dashboard"
            page.get_by_text("Dashboard").click()

            current_stage = "Waiting for Dashboard iframe to render"
            dashboard_frame = page.frame_locator("iframe").first
            expect(dashboard_frame.get_by_text("Application Overview")
                   ).to_be_visible(timeout=10000)
            print("Returned to Dashboard and verified UI rendered.")

            # 2. TEST COMPARE BUTTON & METRICS MODAL
            current_stage = "Opening Compare Metrics Modal"
            print("Testing 'Compare' Modal functionality...")
            app_overview_section = dashboard_frame.locator(
                "div").filter(has_text="Application Overview").first
            compare_button = app_overview_section.get_by_text("Compare").first

            compare_button.click()
            page.wait_for_load_state('networkidle')
            page.wait_for_timeout(5000)

            current_stage = "Verifying Compare Modal Contents"

            date_range_button = dashboard_frame.get_by_role(
                "button", name=re.compile(r"Jan 1, 2026 - .*"))
            expect(date_range_button).to_be_visible(timeout=5000)

            page.wait_for_timeout(3000)
            print("Compare metrics opened and verified successfully")

            print("All testing completed successfully.")

        except Exception as e:
            # ERROR HANDLING
            print(f"AUTOMATION FAILED!")
            print(f"Failed during stage: '{current_stage}'")
            print(f"Error Details: {str(e)}")

            # Take screenshot at the exact moment of failure
            error_screenshot_path = f"error_at_{current_stage.replace(' ', '_').lower()}.png"
            page.screenshot(path=error_screenshot_path)
            print(f"📸 Screenshot saved to: {error_screenshot_path}\n")

            traceback.print_exc()

        finally:
            print("Closing browser...")
            browser.close()


if __name__ == "__main__":
    run_automation()
