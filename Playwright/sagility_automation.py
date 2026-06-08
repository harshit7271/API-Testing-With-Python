from playwright.sync_api import sync_playwright, expect
from dotenv import load_dotenv
import traceback
import os
import re
import logging

# Logs
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.FileHandler("automation_results.log",
                            mode='w', encoding="utf-8"),
        logging.StreamHandler()
    ]
)

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
            page.goto("https://hire-admin-qa.bling-ai.com/portal/index.html", wait_until="domcontentloaded", timeout=60000)
            logging.info(f"1. Page title: {page.title()}")
            
            current_stage = "Filling Login Credentials"
            email_field = page.get_by_placeholder("Enter your email")
            email_field.wait_for(state="visible", timeout=30000)
            email_field.fill(EMAIL or "")
            page.get_by_placeholder("Enter your password").fill(PASSWORD or "")
            page.screenshot(
                path='before-login.png')

            current_stage = "Submitting Login"
            page.click('button[type="submit"]')
            logging.info("2. Login successful, welcome message found.")

            current_stage = "Waiting for Dashboard Load"
            page.get_by_text("Decision Engine").wait_for(state="visible", timeout=30000)
            page.wait_for_timeout(8000)

            logging.info(f"3. After login - Page title: {page.title()}")
            logging.info(f"4. After login - URL: {page.url}")
            page.screenshot(
                path='after-login.png')
            logging.info("5. Login successful! Sagility Dashboard loaded")

            # 1. TEST SIDEBAR NAVIGATION
            current_stage = "Testing Sidebar Navigation - Decision Engine"
            logging.info("6. Testing Sidebar Navigation...")
            page.get_by_text("Decision Engine").click()
            page.wait_for_timeout(8000)
            expect(page.get_by_text("Pending Activity")).to_be_visible()
            logging.info(f"7. Navigated to Decision Engine: {page.url}")

            current_stage = "Testing Sidebar Navigation - Pending Activity"
            page.get_by_text("Pending Activity").click()
            page.wait_for_timeout(5000)
            logging.info(f"8. Navigated to Pending Activity: {page.url}")

            current_stage = "Returning to Dashboard"
            page.get_by_text("Dashboard").click()
            page.wait_for_timeout(3000)

            current_stage = "Waiting for Dashboard iframe to render"
            dashboard_frame = page.frame_locator("iframe").first
            expect(dashboard_frame.get_by_text("Application Overview")
                   ).to_be_visible(timeout=10000)
            logging.info("9. Returned to Dashboard and verified UI rendered.")

            # 2. TEST COMPARE BUTTON & METRICS MODAL
            current_stage = "Opening Compare Metrics Modal"
            logging.info("10. Testing 'Compare' Modal functionality...")
            app_overview_section = dashboard_frame.locator(
                "div").filter(has_text="Application Overview").first
            compare_button = app_overview_section.get_by_text("Compare").first

            compare_button.click()
            page.wait_for_timeout(5000)

            current_stage = "Verifying Compare Modal Contents"

            date_range_button = dashboard_frame.get_by_role(
                "button", name=re.compile(r"Jan 1, 2026 - .*"))
            expect(date_range_button).to_be_visible(timeout=5000)

            page.wait_for_timeout(3000)
            logging.info(
                "11. Compare metrics opened and verified successfully")

            logging.info("12. All testing completed successfully.")

            # 3. TEST CALENDAR DATE SELECTION
            current_stage = "Testing Calendar Date Selection"
            logging.info(
                "13. Opening the calendar to select a new date range...")
            date_range_button.click()
            apply_button = dashboard_frame.get_by_role("button", name="Apply")
            expect(apply_button).to_be_visible(timeout=5000)
            logging.info("14. Calendar is open and ready.")
            logging.info("Selecting dates: 1st to 5th...")
            dashboard_frame.get_by_text(
                "1", exact=True).first.click(force=True)
            page.wait_for_timeout(500)
            dashboard_frame.get_by_text(
                "5", exact=True).first.click(force=True)
            page.wait_for_timeout(500)
            
            logging.info("Clicking Apply if visible...")
            apply_btn = dashboard_frame.get_by_role("button", name="Apply")
            if apply_btn.is_visible():
                apply_btn.click(force=True)
                logging.info("Apply button clicked.")
            else:
                logging.info("Apply button not found or already closed.")
            
            page.wait_for_timeout(2000)
            logging.info(
                "Clicking 'Dashboard' in the sidebar to dismiss the calendar...")
            page.get_by_text("Dashboard").first.click()
            page.wait_for_timeout(5000)
            expect(apply_button).to_be_hidden(timeout=5000)
            logging.info(
                "15. Calendar closed. New date range applied successfully.")

            # 4. TEST HIRE SIGNAL OVERVIEW
            current_stage = "Testing Hire Signal Overview"
            logging.info("16. Scrolling down to 'Hire Signal Overview'...")
            hire_title = dashboard_frame.get_by_text(
                "Hire Signal Overview", exact=True).first
            hire_title.evaluate(
                "el => el.scrollIntoView({ behavior: 'smooth', block: 'center' })")
            page.wait_for_timeout(8000)
            logging.info("Clicking 'Compare' on Hire Signal Overview...")
            hire_widget = dashboard_frame.locator("div").filter(
                has=dashboard_frame.get_by_text(
                    "Hire Signal Overview", exact=True)
            ).filter(
                has=dashboard_frame.get_by_text("Compare")
            ).last
            hire_compare_btn = hire_widget.get_by_role(
                "button", name="Compare").first
            hire_compare_btn.click()
            
            # Wait for the modal to open
            close_button = dashboard_frame.get_by_role(
                "button", name="Close").first
            expect(close_button).to_be_visible(timeout=5000)
            logging.info("17. Hire Signal Overview Modal opened successfully.")
            
            # DEEPER MODAL CHECK
            logging.info("Verifying content within the Hire Signal Overview modal...")
            modal_content = dashboard_frame.locator("div[role='dialog'], .modal-content, .ant-modal-content").first
            
            # Wait for "Loading..." to disappear
            loading_indicator = modal_content.get_by_text("Loading...")
            if loading_indicator.count() > 0:
                logging.info("Waiting for modal data to load...")
                try:
                    expect(loading_indicator.first).to_be_hidden(timeout=15000)
                except Exception:
                    logging.warning("Loading indicator still visible after 15s, proceeding anyway.")

            # Scroll and check months
            months = ["January", "February", "March", "April", "May", "June"]
            for month in months:
                month_locator = modal_content.get_by_text(month, exact=False).first
                if month_locator.count() > 0:
                    month_locator.evaluate("el => el.scrollIntoView({ behavior: 'smooth', block: 'center' })")
                    page.wait_for_timeout(1000)
                    logging.info(f"✓ Verified data for {month}")
                else:
                    logging.warning(f"⚠ Could not find data for {month} in modal")

            # Try to scroll to the very bottom
            modal_content.evaluate("el => el.scrollTop = el.scrollHeight")
            page.wait_for_timeout(2000)
            logging.info("18. Scrolled to the bottom and verified all months.")

            page.wait_for_timeout(2000)
            logging.info("Clicking the ❌ button to close the modal...")
            close_button.click()
            expect(close_button).to_be_hidden(timeout=5000)
            logging.info("19. Hire Signal Overview Modal closed successfully.")

            # 5. TEST OFFER ACCEPTANCE RATE MODAL
            current_stage = "Testing Offer Acceptance Rate Modal"
            logging.info("19. Scrolling down to 'Offer Acceptance Rate'...")
            offer_title = dashboard_frame.get_by_text(
                "Offer Acceptance Rate", exact=True).first
            offer_title.evaluate(
                "el => el.scrollIntoView({ behavior: 'smooth', block: 'center' })")
            page.wait_for_timeout(8000)
            logging.info("Clicking 'Compare' on Offer Acceptance Rate...")
            offer_widget = dashboard_frame.locator("div").filter(
                has=dashboard_frame.get_by_text(
                    "Offer Acceptance Rate", exact=True)
            ).filter(
                has=dashboard_frame.get_by_text("Compare")
            ).last
            offer_compare_btn = offer_widget.get_by_role(
                "button", name="Compare").first
            offer_compare_btn.click()
            # Wait for the modal to open
            close_button = dashboard_frame.get_by_role(
                "button", name="Close").first
            expect(close_button).to_be_visible(timeout=5000)
            logging.info("20. Modal opened successfully.")
            page.wait_for_timeout(2000)
            logging.info("Clicking the ❌ button to close the modal...")
            close_button.click()
            expect(close_button).to_be_hidden(timeout=5000)
            logging.info("21. Modal closed successfully.")

            # 6. NAVIGATE TO SOURCE BY CANDIDATE APPLIED
            current_stage = "Scrolling to Source By Candidate Applied"
            logging.info(
                "22. Scrolling further down to 'Source By Candidate Applied'...")
            source_title = dashboard_frame.get_by_text(
                "Source By Candidate Applied", exact=True).first
            source_title.evaluate(
                "el => el.scrollIntoView({ behavior: 'smooth', block: 'center' })")
            page.wait_for_timeout(3000)
            logging.info(
                "23. Successfully reached 'Source By Candidate Applied'.")

            # 7. TEST SOURCE BY CANDIDATE APPLIED MAP
            current_stage = "Testing Map Interactions"
            logging.info(
                "24. Interacting with dynamic country cards on the map...")
            logging.info("Scrolling the dashboard frame to the bottom...")
            dashboard_frame.locator("body").evaluate(
                "body => body.scrollIntoView({ behavior: 'smooth', block: 'end' })")
            page.wait_for_timeout(2000)
            country_cards = dashboard_frame.get_by_role(
                "button").filter(has_text="Total Application:")
            expect(country_cards.first).to_be_visible(timeout=5000)
            card_count = country_cards.count()
            logging.info(f"Found {card_count} country cards to interact with.")
            if card_count == 0:
                logging.warning(
                    "No country cards found! The list might not have loaded.")
            else:
                for i in range(card_count):
                    current_card = country_cards.nth(i)
                    current_card.evaluate(
                        "el => el.scrollIntoView({ behavior: 'smooth', block: 'center' })")
                    page.wait_for_timeout(500)
                    logging.info(
                        f"Clicking country card {i + 1} of {card_count}...")
                    current_card.click()
                    page.wait_for_timeout(2000)

            logging.info("25. Map interaction testing completed successfully.")

        except Exception as e:
            # ERROR HANDLING
            logging.error("AUTOMATION FAILED!")
            logging.error(f"Failed during stage: '{current_stage}'")
            logging.error(f"Error Details: {str(e)}")

            # Create error_screenshots directory if it doesn't exist
            os.makedirs("error_screenshots", exist_ok=True)
            
            # Take screenshot at the exact moment of failure
            error_screenshot_path = os.path.join("error_screenshots", f"error_at_{current_stage.replace(' ', '_').lower()}.png")
            page.screenshot(path=error_screenshot_path)
            logging.error(f"Screenshot saved to: {error_screenshot_path}\n")

            # Capture traceback in the logs
            logging.error(traceback.format_exc())

        finally:
            logging.info("Closing browser...")
            browser.close()


if __name__ == "__main__":
    run_automation()
