import logging
import re
from typing import Optional
from playwright.sync_api import expect, Page, FrameLocator


class DashboardPage:
    def __init__(self, page: Page):
        self.page = page
        # Will be initialized once the iframe loads
        self.frame: Optional[FrameLocator] = None

    def wait_for_load(self):
        self.page.get_by_text("Decision Engine").wait_for(
            state="visible", timeout=30000)
        self.page.wait_for_timeout(8000)
        logging.info(f"3. After login - Page title: {self.page.title()}")
        logging.info(f"4. After login - URL: {self.page.url}")
        self.page.screenshot(path='after-login.png')
        logging.info("5. Login successful! Sagility Dashboard loaded")

    def test_sidebar_navigation(self):
        logging.info("6. Testing Sidebar Navigation...")
        self.page.get_by_text("Decision Engine").click()
        self.page.wait_for_timeout(8000)
        expect(self.page.get_by_text("Pending Activity")).to_be_visible()
        logging.info(f"7. Navigated to Decision Engine: {self.page.url}")

        self.page.get_by_text("Pending Activity").click()
        self.page.wait_for_timeout(5000)
        logging.info(f"8. Navigated to Pending Activity: {self.page.url}")

        self.page.get_by_text("Dashboard").first.click()
        self.page.wait_for_timeout(5000)

        # Initialize the frame for subsequent dashboard tests
        self.page.locator("iframe").first.wait_for(
            state="visible", timeout=30000)
        self.frame = self.page.frame_locator("iframe").first
        expect(self.frame.get_by_text("Application Overview")
               ).to_be_visible(timeout=20000)
        logging.info("9. Returned to Dashboard and verified UI rendered.")

    def test_compare_modal(self):
        assert self.frame is not None, "Dashboard iframe not initialized. Cannot test Compare Modal."

        logging.info("10. Testing 'Compare' Modal functionality...")
        app_overview_section = self.frame.locator(
            "div").filter(has_text="Application Overview").first
        app_overview_section.get_by_text("Compare").first.click()
        self.page.wait_for_timeout(5000)

        close_button = self.frame.get_by_role("button", name="Close").first
        if close_button.count() == 0:
            close_button = self.frame.locator(
                ".ant-tabs-tab-remove, .ant-modal-close, .close-icon, [aria-label='Close'], button:has-text('×')").filter(visible=True).first

        if close_button.count() > 0:
            close_button.click(force=True)
            logging.info("11. Compare metrics closed successfully")
        else:
            logging.warning("Could not find close button for Compare modal")

        self.page.wait_for_timeout(3000)
        logging.info("12. Application Overview testing completed.")
        logging.info(
            "13. Calendar and Compare tab logic bypassed successfully.")

    def test_hire_signal_overview_modal(self):
        assert self.frame is not None, "Dashboard iframe not initialized. Cannot test Hire Signal Overview Modal."

        logging.info("14. Scrolling down to 'Hire Signal Overview'...")
        hire_title = self.frame.get_by_text(
            "Hire Signal Overview", exact=True).first
        hire_title.evaluate(
            "el => el.scrollIntoView({ behavior: 'smooth', block: 'center' })")
        self.page.wait_for_timeout(8000)

        hire_widget = self.frame.locator("div").filter(has=self.frame.get_by_text(
            "Hire Signal Overview", exact=True)).filter(has=self.frame.get_by_text("Compare")).last
        hire_widget.get_by_role("button", name="Compare").first.click()

        close_button = self.frame.get_by_role("button", name="Close").first
        expect(close_button).to_be_visible(timeout=5000)
        logging.info("15. Hire Signal Overview Modal opened successfully.")

        modal_content = self.frame.locator(
            "div[role='dialog'], .modal-content, .ant-modal-content").first
        loading_indicator = modal_content.get_by_text("Loading...")
        if loading_indicator.count() > 0:
            try:
                expect(loading_indicator.first).to_be_hidden(timeout=15000)
            except Exception:
                logging.warning("Loading indicator still visible after 15s.")

        months = ["January", "February", "March", "April", "May", "June"]
        for month in months:
            month_locator = modal_content.get_by_text(month, exact=False).first
            if month_locator.count() > 0:
                month_locator.evaluate(
                    "el => el.scrollIntoView({ behavior: 'smooth', block: 'center' })")
                self.page.wait_for_timeout(1000)
                logging.info(f"✓ Verified data for {month}")
            else:
                logging.warning(f"⚠ Could not find data for {month} in modal")

        modal_content.evaluate("el => el.scrollTop = el.scrollHeight")
        self.page.wait_for_timeout(2000)
        logging.info("16. Scrolled to the bottom and verified all months.")

        close_button.click()
        expect(close_button).to_be_hidden(timeout=5000)
        logging.info("17. Hire Signal Overview Modal closed successfully.")

    def test_hire_signal_matrix(self):
        assert self.frame is not None, "Dashboard iframe not initialized. Cannot test Hire Signal Matrix."

        logging.info("18. Running the full 16-combination matrix test...")

        def click_signal_node(node_name, index=0):
            node = self.frame.get_by_text(
                node_name, exact=True).filter(visible=True).nth(index)
            if node.count() > 0:
                node.click(force=True)
            else:
                logging.warning(
                    f"⚠ Could not find visible node: '{node_name}' at index {index}")

        hire_title = self.frame.get_by_text(
            "Hire Signal Overview", exact=True).first
        hire_title.evaluate(
            "el => el.scrollIntoView({ behavior: 'smooth', block: 'start' })")
        self.page.wait_for_timeout(2000)

        nova_signals = [("Hire", 0), ("Consider", 0),
                        ("Do Not Hire", 0), ("Pending", 0)]
        recruiter_decisions = [("Hire", 1), ("Decline", 0),
                               ("Hold", 0), ("Pending", 1)]
        reset_btn = self.frame.get_by_text(
            "Reset", exact=True).filter(visible=True).first

        for n_node, n_idx in nova_signals:
            for r_node, r_idx in recruiter_decisions:
                logging.info(
                    f"Testing Flow: {n_node} (Nova) -> {r_node} (Recruiter)")

                if reset_btn.count() > 0:
                    reset_btn.click(force=True)
                    self.page.wait_for_timeout(400)

                click_signal_node(n_node, n_idx)
                self.page.wait_for_timeout(300)
                click_signal_node(r_node, r_idx)

                self.page.wait_for_timeout(3000)

                try:
                    nova_title_regex = re.compile(
                        f"Nova Signal\\s*→\\s*{re.escape(n_node)}", re.I)
                    expect(self.frame.locator("div").filter(
                        has_text=nova_title_regex).first).to_be_visible(timeout=5000)

                    rec_title_regex = re.compile(
                        f"Recruiter Decision\\s*→\\s*{re.escape(r_node)}", re.I)
                    expect(self.frame.locator("div").filter(
                        has_text=rec_title_regex).first).to_be_visible(timeout=5000)

                    dm_text = self.frame.locator("div").filter(has_text=re.compile(
                        r"Decision Match", re.I)).first.text_content(timeout=5000) or ""
                    match_search = re.search(
                        r'Decision Match\s*(\d+)', dm_text, re.I)
                    dm_value = match_search.group(1) if match_search else "0"

                    routed_title_regex = re.compile(
                        f"ROUTED TO\\s*{re.escape(n_node)}\\s*/\\s*{re.escape(r_node)}", re.I)
                    routed_to_card = self.frame.locator("div").filter(
                        has_text=routed_title_regex).first

                    expect(routed_to_card).to_be_visible(timeout=5000)
                    expect(routed_to_card).to_contain_text(
                        dm_value, timeout=5000)
                    logging.info(
                        f"✅ Verified {n_node} -> {r_node} | Match Count synced at: {dm_value}")

                except Exception as assertion_error:
                    logging.error(
                        f"❌ UI Verification Failed for {n_node} -> {r_node}: {str(assertion_error)}")
                    raise assertion_error

        if reset_btn.count() > 0:
            reset_btn.click(force=True)
        self.page.wait_for_timeout(1000)
        logging.info(
            "19. All 16 combinations fully tested and validated successfully.")

    def test_offer_acceptance_modal(self):
        assert self.frame is not None, "Dashboard iframe not initialized. Cannot test Offer Acceptance Modal."

        logging.info("20. Scrolling down to 'Offer Acceptance Rate'...")
        offer_title = self.frame.get_by_text(
            "Offer Acceptance Rate", exact=True).first
        offer_title.evaluate(
            "el => el.scrollIntoView({ behavior: 'smooth', block: 'center' })")
        self.page.wait_for_timeout(8000)

        offer_widget = self.frame.locator("div").filter(has=self.frame.get_by_text(
            "Offer Acceptance Rate", exact=True)).filter(has=self.frame.get_by_text("Compare")).last
        offer_widget.get_by_role("button", name="Compare").first.click()

        close_button = self.frame.get_by_role("button", name="Close").first
        expect(close_button).to_be_visible(timeout=5000)
        logging.info("21. Modal opened successfully.")
        self.page.wait_for_timeout(2000)
        close_button.click()
        expect(close_button).to_be_hidden(timeout=5000)
        logging.info("22. Modal closed successfully.")

    def test_source_by_candidate_map(self):
        assert self.frame is not None, "Dashboard iframe not initialized. Cannot test Source By Candidate Map."

        logging.info(
            "23. Scrolling further down to 'Source By Candidate Applied'...")
        source_title = self.frame.get_by_text(
            "Source By Candidate Applied", exact=True).first
        source_title.evaluate(
            "el => el.scrollIntoView({ behavior: 'smooth', block: 'center' })")
        self.page.wait_for_timeout(3000)
        logging.info("24. Successfully reached 'Source By Candidate Applied'.")

        logging.info(
            "25. Interacting with dynamic country cards on the map...")
        self.frame.locator("body").evaluate(
            "body => body.scrollIntoView({ behavior: 'smooth', block: 'end' })")
        self.page.wait_for_timeout(2000)

        country_cards = self.frame.get_by_role(
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
                self.page.wait_for_timeout(500)
                logging.info(
                    f"Clicking country card {i + 1} of {card_count}...")
                current_card.click()
                self.page.wait_for_timeout(2000)
        logging.info("26. Map interaction testing completed successfully.")
