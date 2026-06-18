import os
import traceback
import logging
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

# Import your new modules
from utils import setup_logger
from pages.login_page import LoginPage
from pages.dashboard import DashboardPage

# Initialize environment and logging
setup_logger()
load_dotenv()

EMAIL = os.getenv('EMAIL')
PASSWORD = os.getenv('PASSWORD')
URL = "https://dev-hire-admin.bling-ai.com/portal/index.html"

if EMAIL is None or PASSWORD is None:
    raise ValueError(
        'EMAIL and PASSWORD environment variables must be set in .env file')


def run_automation():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        # Initialize Page Objects
        login_page = LoginPage(page)
        dashboard_page = DashboardPage(page)

        current_stage = "Initialization"

        try:
            current_stage = "Login Process"
            login_page.navigate_and_login(URL, EMAIL, PASSWORD)

            current_stage = "Waiting for Dashboard Load"
            dashboard_page.wait_for_load()

            current_stage = "Testing Sidebar Navigation"
            dashboard_page.test_sidebar_navigation()

            current_stage = "Testing Compare Metrics Modal"
            dashboard_page.test_compare_modal()

            current_stage = "Testing Hire Signal Overview Modal"
            dashboard_page.test_hire_signal_overview_modal()

            current_stage = "Testing Hire Signal Matrix"
            dashboard_page.test_hire_signal_matrix()

            current_stage = "Testing Offer Acceptance Rate Modal"
            dashboard_page.test_offer_acceptance_modal()

            current_stage = "Testing Source By Candidate Map"
            dashboard_page.test_source_by_candidate_map()

            logging.info("\n🎉 AUTOMATION SUITE COMPLETED SUCCESSFULLY 🎉\n")

        except Exception as e:
            logging.error("\n" + "="*50)
            logging.error("!!! AUTOMATION FAILED !!!")
            logging.error("="*50)
            logging.error(f"STAGE OF FAILURE: '{current_stage}'")
            logging.error(f"ERROR TYPE: {type(e).__name__}")
            logging.error(f"DETAILS: {str(e)}")
            logging.error("-" * 50)

            os.makedirs("error_screenshots", exist_ok=True)
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
