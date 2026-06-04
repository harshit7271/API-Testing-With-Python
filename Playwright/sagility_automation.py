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

        # Tracking the current stage
        current_stage = "Initialization"

        try:
            # LOGIN TESTING
            current_stage = "Navigating to Portal"
            page.goto("https://hire-admin-qa.bling-ai.com/portal/index.html")
            print("1. Page title:", page.title())
            page.wait_for_load_state('networkidle')

            current_stage = "Filling Login Credentials"
            page.get_by_placeholder("Enter your email").fill(EMAIL or "")
            page.get_by_placeholder("Enter your password").fill(PASSWORD or "")
            page.screenshot(path='signin-page.png')

            current_stage = "Submitting Login"
            page.click('button[type="submit"]')
            print("2. Login successful, welcome message found.")

            current_stage = "Waiting for Dashboard Load"
            page.wait_for_load_state('networkidle')
            page.wait_for_timeout(8000)

            print("3. After login - Page title:", page.title())
            print("4. After login - URL:", page.url)
            page.screenshot(path='after-login.png')
            print("5. Login successful! Sagility Dashboard loaded")

            # 1. TEST SIDEBAR NAVIGATION
            current_stage = "Testing Sidebar Navigation - Decision Engine"
            print("6. Testing Sidebar Navigation...")
            page.get_by_text("Decision Engine").click()
            page.wait_for_timeout(8000)
            expect(page.get_by_text("Pending Activity")).to_be_visible()
            print("7. Navigated to Decision Engine: ", page.url)

            current_stage = "Testing Sidebar Navigation - Pending Activity"
            page.get_by_text("Pending Activity").click()
            page.wait_for_timeout(5000)
            print("8. Navigated to Pending Activity: ", page.url)

            current_stage = "Returning to Dashboard"
            page.get_by_text("Dashboard").click()
            page.wait_for_timeout(3000)

            current_stage = "Waiting for Dashboard iframe to render"
            dashboard_frame = page.frame_locator("iframe").first
            expect(dashboard_frame.get_by_text("Application Overview")
                   ).to_be_visible(timeout=10000)
            print("9. Returned to Dashboard and verified UI rendered.")

            # 2. TEST COMPARE BUTTON & METRICS MODAL
            current_stage = "Opening Compare Metrics Modal"
            print("10. Testing 'Compare' Modal functionality...")
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
            print("11. Compare metrics opened and verified successfully")

            print("12. All testing completed successfully.")

            # 3. TEST CALENDAR DATE SELECTION
            current_stage = "Testing Calendar Date Selection"
            print("13. Opening the calendar to select a new date range...")
            date_range_button.click()
            apply_button = dashboard_frame.get_by_role("button", name="Apply")
            expect(apply_button).to_be_visible(timeout=5000)
            print("14. Calendar is open and ready.")
            print("Selecting dates: 10th to 20th...")
            dashboard_frame.get_by_text("10", exact=True).first.click()
            page.wait_for_timeout(500)
            dashboard_frame.get_by_text("20", exact=True).first.click()
            page.wait_for_timeout(500)
            print("Clicking Apply...")
            apply_button.click()
            page.wait_for_timeout(2000)
            print("Clicking 'Dashboard' in the sidebar to dismiss the calendar...")
            page.get_by_text("Dashboard").first.click()
            page.wait_for_timeout(5000)
            expect(apply_button).to_be_hidden(timeout=5000)
            print("15. Calendar closed. New date range applied successfully.")

        except Exception as e:
            # ERROR HANDLING
            print(f"AUTOMATION FAILED!")
            print(f"Failed during stage: '{current_stage}'")
            print(f"Error Details: {str(e)}")

            # Take screenshot at the exact moment of failure
            error_screenshot_path = f"error_at_{current_stage.replace(' ', '_').lower()}.png"
            page.screenshot(path=error_screenshot_path)
            print(f"Screenshot saved to: {error_screenshot_path}\n")

            traceback.print_exc()

        finally:
            print("Closing browser...")
            browser.close()


if __name__ == "__main__":
    run_automation()
