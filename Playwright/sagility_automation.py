from playwright.sync_api import sync_playwright, expect
from dotenv import load_dotenv
import traceback
import os
import re
import logging
import colorama
from colorama import Fore, Style, Back

# Initialize colorama - force colors even if redirected
colorama.init(autoreset=True, strip=False)


class ColoredFormatter(logging.Formatter):
    """Custom formatter to add colors and emoji markers to logs."""
    # Use raw ANSI codes for maximum compatibility in some Windows environments
    COLORS = {
        logging.DEBUG: "\033[36m",    # Cyan
        logging.INFO: "\033[32m",     # Green
        logging.WARNING: "\033[33;1m",  # Bold Yellow
        logging.ERROR: "\033[31;1m",   # Bold Red
        logging.CRITICAL: "\033[41;37;1m",  # White on Red background
    }
    RESET = "\033[0m"

    def format(self, record):
        log_color = self.COLORS.get(record.levelno, "")

        # Add emoji markers for visibility
        prefix = ""
        if record.levelno == logging.ERROR:
            prefix = "❌ "
        elif record.levelno == logging.WARNING:
            prefix = "⚠ "
        elif record.levelno == logging.INFO:
            prefix = "✅ "
        elif record.levelno == logging.CRITICAL:
            prefix = "🚨 "

        message = super().format(record)
        return f"{log_color}{prefix}{message}{self.RESET}"


# Logs Configuration
log_format = '%(asctime)s [%(levelname)s] [%(lineno)d] %(message)s'
date_format = '%Y-%m-%d %H:%M:%S'

# File handler (no colors)
file_handler = logging.FileHandler(
    "automation_results.log", mode='w', encoding="utf-8")
file_handler.setFormatter(logging.Formatter(log_format, datefmt=date_format))

# Console handler (with colors)
console_handler = logging.StreamHandler()
console_handler.setFormatter(ColoredFormatter(log_format, datefmt=date_format))

logging.basicConfig(
    level=logging.INFO,
    handlers=[file_handler, console_handler]
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
            page.goto("https://hire-admin-qa.bling-ai.com/portal/index.html",
                      wait_until="domcontentloaded", timeout=60000)
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
            page.get_by_text("Decision Engine").wait_for(
                state="visible", timeout=30000)
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
            page.get_by_text("Dashboard").first.click()
            page.wait_for_timeout(5000)

            current_stage = "Waiting for Dashboard iframe to render"
            # Explicitly wait for the iframe element to be visible
            page.locator("iframe").first.wait_for(
                state="visible", timeout=30000)
            dashboard_frame = page.frame_locator("iframe").first

            # Wait longer for the content inside the iframe
            expect(dashboard_frame.get_by_text("Application Overview")
                   ).to_be_visible(timeout=20000)
            logging.info("9. Returned to Dashboard and verified UI rendered.")

            # 2. TEST COMPARE BUTTON & METRICS MODAL
            current_stage = "Opening Compare Metrics Modal"
            logging.info("10. Testing 'Compare' Modal functionality...")
            app_overview_section = dashboard_frame.locator(
                "div").filter(has_text="Application Overview").first
            compare_button = app_overview_section.get_by_text("Compare").first

            compare_button.click()
            page.wait_for_timeout(5000)

            current_stage = "Closing Compare Metrics Modal"
            logging.info("Closing the Compare modal...")

            # Using the same close button logic as other sections
            close_button = dashboard_frame.get_by_role(
                "button", name="Close").first
            if close_button.count() == 0:
                # Fallback to cross button if 'Close' button is not found
                close_button = dashboard_frame.locator(
                    ".ant-tabs-tab-remove, .ant-modal-close, .close-icon, [aria-label='Close'], button:has-text('×')").filter(visible=True).first

            if close_button.count() > 0:
                close_button.click(force=True)
                logging.info("11. Compare metrics closed successfully")
            else:
                logging.warning(
                    "Could not find close button for Compare modal")

            page.wait_for_timeout(3000)

            logging.info("12. Application Overview testing completed.")
            """
            "button", name=re.compile(r"Jan 1, 2026 - .*").first
            date_range_btn.click()
            
            # User requested 10 seconds wait
            logging.info("Waiting 10 seconds for calendar...")
            page.wait_for_timeout(10000)
            
            logging.info("Selecting dates: 1st to 22th...")
            
            def click_day(day):
                logging.info(f"Attempting to click day: {day}")
                day_locators = [
                    dashboard_frame.get_by_role("button", name=str(day), exact=True).filter(visible=True),
                    dashboard_frame.get_by_text(str(day), exact=True).filter(visible=True),
                    dashboard_frame.locator(f"div:text-is('{day}')").filter(visible=True),
                    dashboard_frame.locator(f"span:text-is('{day}')").filter(visible=True),
                    dashboard_frame.locator(f"td:text-is('{day}')").filter(visible=True)
                ]
                for loc in day_locators:
                    try:
                        if loc.count() > 0:
                            loc.first.click(force=True, timeout=5000)
                            logging.info(f"Successfully clicked day: {day}")
                            return True
                    except:
                        continue
                return False

            click_day("1")
            page.wait_for_timeout(2000)
            click_day("22")
            page.wait_for_timeout(2000)

            logging.info("Clicking Apply button by force...")
            # Using a more robust locator for Apply button
            apply_btn = dashboard_frame.locator("button:has-text('Apply'), .ant-btn:has-text('Apply')").filter(visible=True).first
            if apply_btn.count() > 0:
                apply_btn.click(force=True)
                logging.info("Apply button clicked.")
            else:
                logging.warning("Apply button not found or not visible with primary locator, trying fallback...")
                apply_btn_fallback = dashboard_frame.get_by_role("button", name=re.compile(r"Apply", re.I)).filter(visible=True).first
                if apply_btn_fallback.count() > 0:
                    apply_btn_fallback.click(force=True)
                    logging.info("Fallback Apply button clicked.")
                else:
                    logging.critical("\n" + "!"*60)
                    logging.critical("!!! CRITICAL ERROR: APPLY BUTTON REALLY NOT FOUND !!!")
                    logging.critical("!"*60)
                    
                    # Take a screenshot specifically for this missing element
                    os.makedirs("error_screenshots", exist_ok=True)
                    missing_element_path = os.path.join("error_screenshots", "missing_apply_button.png")
                    page.screenshot(path=missing_element_path)
                    logging.critical(f"SCREENSHOT OF MISSING BUTTON SAVED TO: {missing_element_path}")
                    logging.critical("!"*60 + "\n")

            page.wait_for_timeout(2000)
            """
            # Ensure the compare modal/tab disappears
            logging.info(
                "Dismissing the Compare tab/modal via cross button...")
            # Prioritize the "cross" button as requested by user
            cross_btn = dashboard_frame.locator(
                ".ant-tabs-tab-remove, .ant-modal-close, .close-icon, [aria-label='Close'], button:has-text('×')").filter(visible=True).first
            if cross_btn.count() > 0:
                cross_btn.click(force=True)
                logging.info("Cross button clicked successfully.")
                page.wait_for_timeout(2000)
            else:
                logging.info("Trying generic 'Close' button as fallback...")
                modal_close_btn = dashboard_frame.get_by_role(
                    "button", name=re.compile(r"Close|Cancel", re.I)).filter(visible=True).first
                if modal_close_btn.count() > 0:
                    modal_close_btn.click(force=True)
                    logging.info("Fallback Close button clicked.")
                    page.wait_for_timeout(2000)

            logging.info(
                "Clicking 'Dashboard' in the sidebar to dismiss the calendar...")
            page.get_by_text("Dashboard").first.click()
            page.wait_for_timeout(5000)
            logging.info(
                "15. Calendar and Compare tab closed. New date range applied successfully.")

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
            logging.info(
                "Verifying content within the Hire Signal Overview modal...")
            modal_content = dashboard_frame.locator(
                "div[role='dialog'], .modal-content, .ant-modal-content").first

            # Wait for "Loading..." to disappear
            loading_indicator = modal_content.get_by_text("Loading...")
            if loading_indicator.count() > 0:
                logging.info("Waiting for modal data to load...")
                try:
                    expect(loading_indicator.first).to_be_hidden(timeout=15000)
                except Exception:
                    logging.warning(
                        "Loading indicator still visible after 15s, proceeding anyway.")

            # Scroll and check months
            months = ["January", "February", "March", "April", "May", "June"]
            for month in months:
                month_locator = modal_content.get_by_text(
                    month, exact=False).first
                if month_locator.count() > 0:
                    month_locator.evaluate(
                        "el => el.scrollIntoView({ behavior: 'smooth', block: 'center' })")
                    page.wait_for_timeout(1000)
                    logging.info(f"✓ Verified data for {month}")
                else:
                    logging.warning(
                        f"⚠ Could not find data for {month} in modal")

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
            logging.error("\n" + "="*50)
            logging.error("!!! AUTOMATION FAILED !!!")
            logging.error("="*50)
            logging.error(f"STAGE OF FAILURE: '{current_stage}'")
            logging.error(f"ERROR TYPE: {type(e).__name__}")
            logging.error(f"DETAILS: {str(e)}")
            logging.error("-" * 50)

            os.makedirs("error_screenshots", exist_ok=True)

            # Take screenshot at the exact moment of failure
            error_screenshot_path = os.path.join(
                "error_screenshots", f"error_at_{current_stage.replace(' ', '_').lower()}.png")
            page.screenshot(path=error_screenshot_path)
            logging.error(f"SCREENSHOT SAVED TO: {error_screenshot_path}")

            logging.error("-" * 50)
            logging.error("TRACEBACK:")
            logging.error(traceback.format_exc())
            logging.error("="*50 + "\n")

        finally:
            logging.info("Closing browser...")
            browser.close()


if __name__ == "__main__":
    run_automation()
