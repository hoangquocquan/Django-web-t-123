"""Focused Owner UAT for Phase 6C accessibility, session, role, and layout boundaries."""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait

BASE_URL = os.environ.get("PHASE6C_BASE_URL", "http://127.0.0.1:8443")
PASSWORD = os.environ.get("PHASE6B_E2E_PASSWORD", "")
USERS = {
    "Admin": "phase6b.admin@example.invalid",
    "Sales": "phase6b.sales@example.invalid",
    "Manager": "phase6b.manager@example.invalid",
}


@dataclass(frozen=True)
class LayoutEvidence:
    width: int
    height: int
    zoom_percent: int
    overflow_pixels: int


def exact_button(driver, label):
    return next(
        (
            button
            for button in driver.find_elements(By.TAG_NAME, "button")
            if button.is_displayed()
            and " ".join((button.get_attribute("textContent") or "").split()) == label
        ),
        None,
    )


def wait_button(wait, label):
    return wait.until(lambda driver: exact_button(driver, label))


def wait_option_containing(wait, selector, fragment):
    return wait.until(
        lambda driver: next(
            (
                option
                for option in driver.find_elements(By.CSS_SELECTOR, selector)
                if fragment in option.text
            ),
            None,
        )
    )


def login(driver, wait, role, password=PASSWORD):
    driver.get(f"{BASE_URL}/#/admin-login")
    email = wait.until(
        ec.visibility_of_element_located((By.CSS_SELECTOR, "input[type='email']"))
    )
    email.clear()
    email.send_keys(USERS[role])
    secret = driver.find_element(By.CSS_SELECTOR, "input[type='password']")
    secret.send_keys(password)
    driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
    wait.until(
        lambda current: (
            "#/admin" in current.current_url
            and "admin-login" not in current.current_url
        )
    )
    wait_button(wait, "Đăng xuất")


def logout(driver, wait):
    wait_button(wait, "Đăng xuất").click()
    wait.until(
        ec.visibility_of_element_located((By.CSS_SELECTOR, "input[type='email']"))
    )


def open_canonical(driver, wait, tab="RFQ"):
    driver.get(f"{BASE_URL}/#/sales-quotes")
    root = wait.until(
        ec.visibility_of_element_located(
            (By.CSS_SELECTOR, "[data-testid='canonical-workflow']")
        )
    )
    if tab != "RFQ":
        wait_button(wait, tab).click()
    return root


def audit_accessible_names(driver):
    return driver.execute_script(
        r"""
        const root = document.querySelector("[data-testid='canonical-workflow']");
        if (!root) return ["missing canonical root"];
        const visible = (element) => {
          const style = getComputedStyle(element);
          const rect = element.getBoundingClientRect();
          return style.display !== "none" && style.visibility !== "hidden" &&
            rect.width > 0 && rect.height > 0;
        };
        const name = (element) => {
          const aria = element.getAttribute("aria-label");
          if (aria && aria.trim()) return aria.trim();
          const labelledBy = element.getAttribute("aria-labelledby");
          if (labelledBy) {
            const text = labelledBy.split(/\s+/).map((id) =>
              document.getElementById(id)?.textContent || ""
            ).join(" ").trim();
            if (text) return text;
          }
          if (element.labels?.length) {
            const text = Array.from(element.labels).map((label) => label.textContent || "")
              .join(" ").trim();
            if (text) return text;
          }
          if (element.tagName === "BUTTON" || element.tagName === "A") {
            return (element.textContent || "").trim();
          }
          return "";
        };
        return Array.from(root.querySelectorAll("button,input,select,textarea,a[href]"))
          .filter(visible)
          .filter((element) => !name(element))
          .map((element) => element.outerHTML.slice(0, 180));
        """
    )


def assert_keyboard_focus_visible(driver, wait):
    rfq_tab = wait_button(wait, "RFQ")
    rfq_tab.click()
    rfq_tab.send_keys(Keys.TAB)
    evidence = driver.execute_script(
        """
        const element = document.activeElement;
        const style = getComputedStyle(element);
        return {
          tag: element?.tagName || "",
          name: (element?.textContent || element?.getAttribute?.("aria-label") || "").trim(),
          outline: style.outlineStyle,
          outlineWidth: style.outlineWidth,
          boxShadow: style.boxShadow,
        };
        """
    )
    has_outline = evidence["outline"] != "none" and evidence["outlineWidth"] != "0px"
    has_ring = evidence["boxShadow"] != "none"
    if evidence["tag"] not in {"BUTTON", "INPUT", "SELECT", "TEXTAREA", "A"}:
        raise AssertionError(f"Keyboard focus did not reach a control: {evidence}")
    if not (has_outline or has_ring):
        raise AssertionError(f"Keyboard focus is not visibly styled: {evidence}")
    return evidence


def assert_responsive_layout(driver, wait):
    evidence = []
    for width, height, zoom_percent in (
        (1440, 1000, 100),
        (1024, 768, 100),
        (768, 900, 100),
        (1024, 768, 200),
    ):
        driver.set_window_size(width, height)
        driver.execute_script(f"document.documentElement.style.zoom='{zoom_percent}%'")
        root = wait.until(
            ec.visibility_of_element_located(
                (By.CSS_SELECTOR, "[data-testid='canonical-workflow']")
            )
        )
        driver.execute_script("arguments[0].scrollIntoView({block: 'start'})", root)
        overflow = driver.execute_script(
            "return Math.max(0, document.documentElement.scrollWidth - "
            "document.documentElement.clientWidth)"
        )
        if overflow > 2:
            raise AssertionError(
                f"Canonical workflow overflows the page at {width}x{height}, "
                f"zoom {zoom_percent}%: {overflow}px"
            )
        for label in ("RFQ", "Quotation lifecycle", "Order progress & audit"):
            button = wait_button(wait, label)
            rect = button.rect
            if rect["width"] <= 0 or rect["height"] <= 0:
                raise AssertionError(f"Workspace control is unusable: {label}")
        evidence.append(LayoutEvidence(width, height, zoom_percent, overflow))
    driver.execute_script("document.documentElement.style.zoom='100%'")
    driver.set_window_size(1440, 1000)
    return evidence


def assert_invalid_login_is_sanitized(driver, wait):
    driver.get(f"{BASE_URL}/#/admin-login")
    driver.find_element(By.CSS_SELECTOR, "input[type='email']").send_keys(
        USERS["Sales"]
    )
    driver.find_element(By.CSS_SELECTOR, "input[type='password']").send_keys(
        "intentionally-wrong-fictional-password"
    )
    driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
    alert = wait.until(
        ec.visibility_of_element_located((By.CSS_SELECTOR, "[role='alert']"))
    )
    if alert.text.strip() != "Đăng nhập bị từ chối.":
        raise AssertionError(f"Authentication error was not sanitized: {alert.text!r}")
    if driver.find_element(By.CSS_SELECTOR, "input[type='password']").get_attribute(
        "value"
    ):
        raise AssertionError("Rejected password remained in the form")


def main():
    if not PASSWORD:
        raise RuntimeError("PHASE6B_E2E_PASSWORD is required in the current process")

    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--window-size=1440,1000")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-first-run")
    driver = webdriver.Chrome(options=options)
    wait = WebDriverWait(driver, 20)
    try:
        assert_invalid_login_is_sanitized(driver, wait)

        login(driver, wait, "Sales")
        open_canonical(driver, wait)
        wait_option_containing(wait, "select option", "CUS-PHASE6B-E2E")
        sales_create = wait_button(wait, "+ RFQ nháp")
        if not sales_create.is_enabled():
            raise AssertionError("Sales-only authoring control is not usable for Sales")
        if exact_button(driver, "Bắt đầu technical review"):
            raise AssertionError("Manager-only review control was exposed to Sales")
        unnamed = audit_accessible_names(driver)
        if unnamed:
            raise AssertionError(f"Unnamed visible canonical controls: {unnamed}")
        focus_evidence = assert_keyboard_focus_visible(driver, wait)
        layout_evidence = assert_responsive_layout(driver, wait)

        driver.get(f"{BASE_URL}/#/sales")
        wait.until(lambda current: "Tổng quan kinh doanh" in current.page_source)
        driver.back()
        wait.until(
            ec.visibility_of_element_located(
                (By.CSS_SELECTOR, "[data-testid='canonical-workflow']")
            )
        )
        if not exact_button(driver, "Đăng xuất"):
            raise AssertionError("Back navigation lost the active memory session")
        driver.forward()
        wait.until(lambda current: "Tổng quan kinh doanh" in current.page_source)
        if not exact_button(driver, "Đăng xuất"):
            raise AssertionError("Forward navigation lost the active memory session")

        open_canonical(driver, wait)
        driver.refresh()
        wait.until(lambda current: exact_button(current, "Đăng nhập"))
        if exact_button(driver, "Đăng xuất"):
            raise AssertionError("Hard refresh incorrectly retained the bearer session")
        wait_button(wait, "Đăng nhập").click()
        login(driver, wait, "Sales")
        open_canonical(driver, wait)
        project = driver.find_element(
            By.XPATH,
            "//label[.//span[normalize-space(.)='Dự án']]//input",
        )
        if project.get_attribute("value"):
            raise AssertionError("Mutable RFQ form state crossed the refreshed session")
        logout(driver, wait)

        login(driver, wait, "Manager")
        open_canonical(driver, wait)
        manager_create = wait_button(wait, "+ RFQ nháp")
        if manager_create.is_enabled():
            raise AssertionError("Sales-only authoring control was usable by Manager")
        wait_button(wait, "Order progress & audit").click()
        if not wait_button(wait, "Refresh"):
            raise AssertionError("Manager global-audit control is missing")
        unnamed = audit_accessible_names(driver)
        if unnamed:
            raise AssertionError(f"Unnamed Manager controls: {unnamed}")
        logout(driver, wait)

        login(driver, wait, "Admin")
        open_canonical(driver, wait)
        if not wait_button(wait, "+ RFQ nháp").is_enabled():
            raise AssertionError("Intended Admin RFQ demo capability is unavailable")
        project = driver.find_element(
            By.XPATH,
            "//label[.//span[normalize-space(.)='Dự án']]//input",
        )
        if project.get_attribute("value"):
            raise AssertionError(
                "Mutable Manager/Sales state leaked into Admin session"
            )
        logout(driver, wait)

        print(
            "PHASE6C_OWNER_UAT_PASS "
            f"accessible_names=pass focus={focus_evidence['tag']} "
            f"layouts={len(layout_evidence)} session_boundary=pass roles=pass"
        )
        return 0
    finally:
        driver.quit()


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (AssertionError, RuntimeError, TimeoutException) as exc:
        print(
            f"PHASE6C_OWNER_UAT_FAIL: {type(exc).__name__}: {exc}",
            file=sys.stderr,
        )
        raise
