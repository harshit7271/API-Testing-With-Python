import logging


class LoginPage:
    def __init__(self, page):
        self.page = page

    def navigate_and_login(self, url, email, password):
        logging.info("1. Navigating to Portal...")
        self.page.goto(url, wait_until="domcontentloaded", timeout=60000)
        logging.info(f"Page title: {self.page.title()}")

        logging.info("Filling Login Credentials...")
        email_field = self.page.get_by_placeholder("Enter your email")
        email_field.wait_for(state="visible", timeout=30000)
        email_field.fill(email)
        self.page.get_by_placeholder("Enter your password").fill(password)
        self.page.screenshot(path='before-login.png')

        logging.info("Submitting Login...")
        self.page.click('button[type="submit"]')
        logging.info("2. Login successful, waiting for dashboard.")
