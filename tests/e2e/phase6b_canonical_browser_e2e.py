"""Live PostgreSQL browser proof for the canonical Phase 6B workflow.

The fixture password is supplied through PHASE6B_E2E_PASSWORD and is never
printed or persisted by this runner. All workflow mutations happen in the UI.
"""

from __future__ import annotations

import os
import sys
import uuid
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import Select, WebDriverWait

BASE_URL = os.getenv("PHASE6B_BASE_URL", "http://127.0.0.1:8443").rstrip("/")
PASSWORD = os.getenv("PHASE6B_E2E_PASSWORD", "")
USERS = {
    "Admin": "phase6b.admin@example.invalid",
    "Sales": "phase6b.sales@example.invalid",
    "Manager": "phase6b.manager@example.invalid",
}


def exact_button(driver, label):
    return driver.find_element(
        By.XPATH,
        f"//button[normalize-space(.)={label!r} and not(@disabled)]",
    )


def wait_button(wait, label):
    return wait.until(lambda driver: exact_button(driver, label))


def select_option_containing(wait, element, fragment):
    option = wait.until(
        lambda _driver: next(
            (
                candidate
                for candidate in Select(element).options
                if fragment in candidate.text
            ),
            None,
        )
    )
    Select(element).select_by_value(option.get_attribute("value"))


def field_by_label(driver, label):
    return driver.find_element(
        By.XPATH,
        f"//label[.//span[normalize-space(.)={label!r}]]//*[self::input or self::textarea or self::select]",
    )


def replace(element, value):
    element.clear()
    element.send_keys(value)


def replace_date(driver, element, value):
    driver.execute_script(
        """
        const setter = Object.getOwnPropertyDescriptor(
          HTMLInputElement.prototype, "value"
        ).set;
        setter.call(arguments[0], arguments[1]);
        arguments[0].dispatchEvent(new Event("input", { bubbles: true }));
        arguments[0].dispatchEvent(new Event("change", { bubbles: true }));
        """,
        element,
        value,
    )
    if element.get_attribute("value") != value:
        raise AssertionError("Date control did not accept the requested value")


def login(driver, wait, role):
    driver.get(f"{BASE_URL}/#/admin-login")
    wait.until(
        ec.visibility_of_element_located((By.CSS_SELECTOR, "input[type='email']"))
    ).send_keys(USERS[role])
    driver.find_element(By.CSS_SELECTOR, "input[type='password']").send_keys(PASSWORD)
    exact_button(driver, "Đăng nhập").click()
    wait.until(
        lambda current: (
            "#/admin" in current.current_url
            and "admin-login" not in current.current_url
        )
    )


def logout(driver, wait):
    wait_button(wait, "Đăng xuất").click()
    wait.until(
        ec.visibility_of_element_located((By.CSS_SELECTOR, "input[type='email']"))
    )


def open_quotes(driver, wait, tab="RFQ"):
    driver.get(f"{BASE_URL}/#/sales-quotes")
    wait.until(lambda current: "Báo giá" in current.page_source)
    if tab != "RFQ":
        wait_button(wait, tab).click()


def open_rfq(driver, wait, project):
    row = wait.until(
        ec.element_to_be_clickable(
            (By.XPATH, f"//tr[td[normalize-space(.)={project!r}]]")
        )
    )
    row.find_element(By.CSS_SELECTOR, "td:first-child button").click()
    wait.until(
        lambda current: (
            project in field_by_label(current, "Dự án").get_attribute("value")
        )
    )


def open_quotation(driver, wait, rfq_number, status):
    selector = (
        f"[data-rfq-number='{rfq_number}'] button[data-quotation-status='{status}']"
    )
    wait.until(ec.element_to_be_clickable((By.CSS_SELECTOR, selector))).click()
    wait.until(
        ec.visibility_of_element_located(
            (
                By.CSS_SELECTOR,
                f"[data-testid='quotation-workspace-detail'][data-quotation-status='{status}']",
            )
        )
    )


def main():
    if len(PASSWORD) < 12:
        raise RuntimeError(
            "PHASE6B_E2E_PASSWORD is required and must contain at least 12 characters"
        )

    marker = uuid.uuid4().hex[:10]
    project = f"PHASE6B-E2E-{marker}"
    today = datetime.now(ZoneInfo("Asia/Tokyo")).date()
    quote_due = (today + timedelta(days=20)).isoformat()
    delivery = (today + timedelta(days=50)).isoformat()
    valid_until = (today + timedelta(days=15)).isoformat()

    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--window-size=1600,1200")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    driver = webdriver.Chrome(options=options)
    wait = WebDriverWait(driver, 20)

    try:
        login(driver, wait, "Sales")
        open_quotes(driver, wait)
        select_option_containing(
            wait,
            field_by_label(driver, "Khách hàng"),
            "CUS-PHASE6B-E2E",
        )
        replace(field_by_label(driver, "Dự án"), project)
        replace(
            field_by_label(driver, "Ghi chú"), "Fictional Phase 6B browser workflow"
        )
        replace_date(driver, field_by_label(driver, "Hạn báo giá"), quote_due)
        replace_date(driver, field_by_label(driver, "Ngày giao hàng"), delivery)
        wait_button(wait, "Tạo bản nháp").click()
        rfq_heading = wait.until(
            lambda current: next(
                (
                    item
                    for item in current.find_elements(By.CSS_SELECTOR, "h3")
                    if item.text.startswith("RFQ-")
                ),
                None,
            )
        )
        rfq_number = rfq_heading.text

        # A hard refresh must drop the memory-only token. Re-login and prove the
        # already-created RFQ is recovered, not recreated.
        driver.refresh()
        wait.until(lambda current: "Đăng nhập để quản lý RFQ" in current.page_source)
        login(driver, wait, "Sales")
        open_quotes(driver, wait)
        matching_rows = wait.until(
            lambda current: current.find_elements(
                By.XPATH, f"//tr[td[normalize-space(.)={project!r}]]"
            )
        )
        if len(matching_rows) != 1:
            raise AssertionError(
                "RFQ refresh/reconciliation created or exposed a duplicate"
            )
        open_rfq(driver, wait, project)

        select_option_containing(
            wait,
            field_by_label(driver, "Part canonical"),
            "PART-PHASE6B-E2E",
        )
        select_option_containing(
            wait,
            field_by_label(driver, "Vật liệu canonical"),
            "MAT-PHASE6B-E2E",
        )
        replace(field_by_label(driver, "Mô tả chi tiết"), "Fictional precision bracket")
        replace(field_by_label(driver, "Số lượng"), "12.0000")
        replace_date(driver, field_by_label(driver, "Ngày giao"), delivery)
        replace(field_by_label(driver, "Dung sai"), "±0.010 mm")
        replace(
            field_by_label(driver, "Ghi chú kỹ thuật"),
            "Deburr and inspect all critical dimensions",
        )
        wait_button(wait, "Thêm dòng").click()
        wait.until(lambda current: "Fictional precision bracket" in current.page_source)
        wait_button(wait, "Sửa").click()
        replace(
            field_by_label(driver, "Mô tả chi tiết"),
            "Fictional precision bracket revised",
        )
        wait_button(wait, "Lưu dòng").click()
        wait.until(
            lambda current: "Fictional precision bracket revised" in current.page_source
        )
        wait_button(wait, "Gửi RFQ sang SUBMITTED").click()
        wait.until(lambda current: "SUBMITTED" in current.page_source)
        logout(driver, wait)

        login(driver, wait, "Manager")
        open_quotes(driver, wait)
        open_rfq(driver, wait, project)
        wait_button(wait, "Bắt đầu technical review").click()
        wait.until(lambda current: "UNDER_REVIEW" in current.page_source)
        wait_button(wait, "Xác nhận READY_TO_QUOTE").click()
        wait.until(lambda current: "READY_TO_QUOTE" in current.page_source)
        logout(driver, wait)

        login(driver, wait, "Sales")
        open_quotes(driver, wait, "Quotation lifecycle")
        Select(
            wait.until(
                ec.element_to_be_clickable(
                    (By.CSS_SELECTOR, "[data-testid='quotation-rfq-selector']")
                )
            )
        ).select_by_visible_text(f"{rfq_number} · {project}")
        wait.until(
            ec.element_to_be_clickable(
                (By.CSS_SELECTOR, "[data-testid='quotation-unit-price']")
            )
        )
        replace_date(
            driver,
            driver.find_element(
                By.CSS_SELECTOR, "[data-testid='quotation-valid-until']"
            ),
            valid_until,
        )
        replace(
            driver.find_element(
                By.CSS_SELECTOR, "[data-testid='quotation-unit-price']"
            ),
            "125000.0000",
        )
        wait_button(wait, "Tạo quotation R0").click()
        wait.until(
            lambda current: (
                "DRAFT" in current.page_source and "QT-" in current.page_source
            )
        )
        wait_button(wait, "Gửi phê duyệt").click()
        wait.until(lambda current: "PENDING_APPROVAL" in current.page_source)
        logout(driver, wait)

        login(driver, wait, "Manager")
        open_quotes(driver, wait, "Quotation lifecycle")
        open_quotation(driver, wait, rfq_number, "PENDING_APPROVAL")
        if driver.find_elements(
            By.XPATH, "//button[normalize-space(.)='Ghi nhận SENT']"
        ):
            raise AssertionError("Manager received a Sales-only quotation command")
        wait_button(wait, "Phê duyệt").click()
        wait.until(lambda current: "APPROVED" in current.page_source)
        logout(driver, wait)

        login(driver, wait, "Sales")
        open_quotes(driver, wait, "Quotation lifecycle")
        open_quotation(driver, wait, rfq_number, "APPROVED")
        replace(
            driver.find_element(By.CSS_SELECTOR, "input[placeholder='Người nhận']"),
            "fictional.buyer@example.invalid",
        )
        replace(
            driver.find_element(
                By.CSS_SELECTOR, "textarea[placeholder='Bằng chứng gửi']"
            ),
            "Phase 6B fictional delivery evidence",
        )
        wait_button(wait, "Ghi nhận SENT").click()
        wait.until(lambda current: "SENT" in current.page_source)
        replace(
            driver.find_element(
                By.CSS_SELECTOR, "input[placeholder='Contact snapshot']"
            ),
            "Fictional Buyer",
        )
        replace(
            driver.find_element(
                By.CSS_SELECTOR, "textarea[placeholder='Decision evidence']"
            ),
            "Fictional signed acceptance",
        )
        wait_button(wait, "Khách hàng chấp nhận").click()
        wait.until(lambda current: "ACCEPTED" in current.page_source)

        wait_button(wait, "Order progress & audit").click()
        selector = wait.until(
            ec.element_to_be_clickable(
                (By.CSS_SELECTOR, "[data-testid='order-conversion-selector']")
            )
        )
        Select(selector).select_by_index(1)
        wait_button(wait, "Convert to Order").click()
        order_heading = wait.until(
            lambda current: next(
                (
                    item
                    for item in current.find_elements(By.CSS_SELECTOR, "h3")
                    if item.text.startswith("SO-")
                ),
                None,
            )
        )
        order_number = order_heading.text
        if "Global audit chỉ dành cho Admin hoặc Manager" not in driver.page_source:
            raise AssertionError("Sales global-audit denial was not rendered")
        logout(driver, wait)

        login(driver, wait, "Manager")
        open_quotes(driver, wait, "Order progress & audit")
        wait.until(
            ec.element_to_be_clickable(
                (By.XPATH, f"//button[contains(., {order_number!r})]")
            )
        ).click()
        wait.until(
            ec.visibility_of_element_located(
                (
                    By.CSS_SELECTOR,
                    f"[data-testid='order-workspace-detail'][data-order-number='{order_number}']",
                )
            )
        )
        replace(
            driver.find_element(
                By.CSS_SELECTOR, "[data-testid='order-progress-input']"
            ),
            "40",
        )
        replace(
            driver.find_element(
                By.CSS_SELECTOR, "[data-testid='order-milestone-input']"
            ),
            "Phase 6B machining started",
        )
        wait_button(wait, "Update progress").click()
        wait.until(
            ec.visibility_of_element_located(
                (
                    By.CSS_SELECTOR,
                    "[data-testid='order-workspace-detail'][data-order-status='IN_PROGRESS'][data-order-progress='40']",
                )
            )
        )
        replace(
            driver.find_element(
                By.CSS_SELECTOR,
                "[data-testid='order-reason-input']",
            ),
            "Fictional quality checkpoint",
        )
        wait_button(wait, "Hold").click()
        wait.until(
            ec.visibility_of_element_located(
                (
                    By.CSS_SELECTOR,
                    "[data-testid='order-workspace-detail'][data-order-status='ON_HOLD']",
                )
            )
        )
        wait_button(wait, "Resume").click()
        wait.until(
            ec.visibility_of_element_located(
                (
                    By.CSS_SELECTOR,
                    "[data-testid='order-workspace-detail'][data-order-status='IN_PROGRESS']",
                )
            )
        )
        wait_button(wait, "Complete 100%").click()
        wait.until(
            ec.visibility_of_element_located(
                (
                    By.CSS_SELECTOR,
                    "[data-testid='order-workspace-detail'][data-order-status='COMPLETED'][data-order-progress='100']",
                )
            )
        )
        if (
            "order.completed" not in driver.page_source
            or "Order audit timeline" not in driver.page_source
        ):
            raise AssertionError("Timeline/global audit evidence is incomplete")

        print(
            "PHASE6B_CANONICAL_BROWSER_E2E_PASS "
            f"project={project} rfq={rfq_number} order={order_number}"
        )
        return 0
    finally:
        driver.quit()


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(
            f"PHASE6B_CANONICAL_BROWSER_E2E_FAIL: {type(exc).__name__}: {exc}",
            file=sys.stderr,
        )
        raise
