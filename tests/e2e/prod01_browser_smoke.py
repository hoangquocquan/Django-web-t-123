"""Selenium smoke test for the PROD-01 Business UI.

The operator supplies local UAT credentials through environment variables. The
script never prints or stores the password.
"""

from __future__ import annotations

import os
import sys
import uuid

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait


def require_environment(name):
    """Return a required environment variable or stop without leaking it."""
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def run():
    """Log in, open the pipeline, submit a CSRF form, and verify the result."""
    base_url = os.getenv("PROD01_BASE_URL", "http://127.0.0.1:8011").rstrip("/")
    email = require_environment("PROD01_UAT_EMAIL")
    password = require_environment("PROD01_UAT_PASSWORD")
    company = f"PROD-01 Browser {uuid.uuid4().hex[:8]}"

    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--window-size=1440,1000")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")

    driver = webdriver.Chrome(options=options)
    wait = WebDriverWait(driver, 15)
    try:
        driver.get(f"{base_url}/admin/login/")
        wait.until(ec.visibility_of_element_located((By.ID, "id_email"))).send_keys(
            email
        )
        driver.find_element(By.ID, "id_password").send_keys(password)
        driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        wait.until(lambda current: "/admin/login/" not in current.current_url)

        driver.get(f"{base_url}/business/leads/")
        wait.until(
            ec.visibility_of_element_located(
                (By.CSS_SELECTOR, "form[action='/business/leads/create/']")
            )
        )
        driver.find_element(
            By.CSS_SELECTOR,
            "form[action='/business/leads/create/'] input[name='company']",
        ).send_keys(company)
        driver.find_element(
            By.CSS_SELECTOR,
            "form[action='/business/leads/create/'] input[name='contact_person']",
        ).send_keys("Browser Buyer")
        driver.find_element(
            By.CSS_SELECTOR,
            "form[action='/business/leads/create/'] button[type='submit']",
        ).click()
        wait.until(lambda current: company in current.page_source)

        if (
            "Lead Pipeline" not in driver.page_source
            or company not in driver.page_source
        ):
            raise AssertionError(
                "Business lead pipeline did not render the submitted lead."
            )
    finally:
        driver.quit()

    print("PROD01_BROWSER_E2E_PASS")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(run())
    except Exception as exc:
        print(f"PROD01_BROWSER_E2E_FAIL: {type(exc).__name__}: {exc}", file=sys.stderr)
        raise
