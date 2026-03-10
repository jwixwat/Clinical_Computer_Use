"""
Persistent Playwright harness skeleton.
"""

from __future__ import annotations

from contextlib import suppress
from dataclasses import dataclass
from pathlib import Path
import re
import subprocess
import time
from typing import Optional
from urllib.error import URLError
from urllib.request import urlopen

from playwright.sync_api import Browser, BrowserContext, Page, Playwright, sync_playwright

from ..config import (
    CHROME_PATH,
    CHROME_PROFILE_DIR,
    DEBUG_URL,
    EMR_BASE_URL,
    EMR_URL_PATTERN,
    MYLE_LOGIN_BUTTON_SELECTOR,
    MYLE_LOGIN_PASSWORD_SELECTOR,
    MYLE_LOGIN_USERNAME_SELECTOR,
    MYLE_PASSWORD,
    MYLE_USERNAME,
)
from ..schemas.contract_types import SurfaceType


@dataclass
class HarnessState:
    browser_connected: bool = False
    active_url: Optional[str] = None
    active_patient_query: Optional[str] = None


class PlaywrightHarness:
    """
    Minimal isolated browser harness.
    """

    def __init__(self) -> None:
        self.state = HarnessState()
        self._playwright: Optional[Playwright] = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self._page: Optional[Page] = None
        self._chrome_proc: Optional[subprocess.Popen] = None
        self._launched_browser: bool = False

    @staticmethod
    def _debug_http_url() -> str:
        return DEBUG_URL.rstrip("/")

    @staticmethod
    def _is_cdp_ready() -> bool:
        try:
            with urlopen(f"{PlaywrightHarness._debug_http_url()}/json/version", timeout=1.5) as response:
                return response.status == 200
        except (URLError, OSError, ValueError):
            return False

    @staticmethod
    def _debug_port() -> str:
        return PlaywrightHarness._debug_http_url().rsplit(":", 1)[-1]

    def _launch_dedicated_chrome(self) -> None:
        Path(CHROME_PROFILE_DIR).mkdir(parents=True, exist_ok=True)
        args = [
            CHROME_PATH,
            f"--user-data-dir={CHROME_PROFILE_DIR}",
            f"--remote-debugging-port={self._debug_port()}",
            "--remote-debugging-address=127.0.0.1",
            "--no-first-run",
            "--no-default-browser-check",
            "--start-maximized",
            EMR_BASE_URL,
        ]
        self._chrome_proc = subprocess.Popen(args)
        self._launched_browser = True

    def _ensure_cdp_browser(self) -> None:
        if self._is_cdp_ready():
            return

        self._launch_dedicated_chrome()
        for _ in range(20):
            if self._is_cdp_ready():
                return
            time.sleep(0.5)
        raise RuntimeError(f"Chrome CDP endpoint did not become ready at {DEBUG_URL}.")

    def connect(self) -> None:
        if self.state.browser_connected:
            return
        self._ensure_cdp_browser()
        self._playwright = sync_playwright().start()
        self._browser = self._playwright.chromium.connect_over_cdp(DEBUG_URL)
        self._context = self._browser.contexts[0] if self._browser.contexts else self._browser.new_context()
        self._close_stale_blank_pages()
        self._page = self._context.new_page()
        self._page.bring_to_front()
        self.state.browser_connected = True

    def _close_stale_blank_pages(self) -> None:
        assert self._context is not None
        for page in list(self._context.pages):
            try:
                if (page.url or "").lower() == "about:blank":
                    page.close()
            except Exception:
                continue

    @property
    def page(self) -> Page:
        if self._page is None:
            raise RuntimeError("Harness is not connected.")
        return self._page

    def open_url(self, url: str) -> None:
        self.page.bring_to_front()
        self.page.goto(url, wait_until="domcontentloaded")
        self._wait_for_myle_app_state()
        self.state.active_url = self.page.url

    def current_url(self) -> str:
        return self.page.url or ""

    def _wait_for_myle_app_state(self, timeout_ms: int = 20000) -> None:
        page = self.page
        deadline = time.time() + (timeout_ms / 1000)
        while time.time() < deadline:
            try:
                if page.locator(MYLE_LOGIN_USERNAME_SELECTOR).count() > 0:
                    return
                if page.locator(MYLE_LOGIN_PASSWORD_SELECTOR).count() > 0:
                    return
                if page.locator("input[placeholder='Search']").count() > 0:
                    return
                if page.locator("body").inner_text().strip():
                    return
            except Exception:
                pass
            page.wait_for_timeout(500)

    def is_myle_context(self) -> bool:
        return EMR_URL_PATTERN.lower() in self.current_url().lower()

    def is_login_page(self) -> bool:
        page = self.page
        url = self.current_url().lower()
        if "medfarsolutions" not in url and not url.startswith(EMR_BASE_URL.lower()):
            return False
        try:
            username = page.locator(MYLE_LOGIN_USERNAME_SELECTOR)
            password = page.locator(MYLE_LOGIN_PASSWORD_SELECTOR)
            return username.count() > 0 and password.count() > 0
        except Exception:
            return False

    def ensure_myle_ready(self) -> None:
        page = self.page
        page.bring_to_front()
        if not self.is_myle_context():
            page.goto(EMR_BASE_URL, wait_until="domcontentloaded")
            self._wait_for_myle_app_state()
        else:
            self._wait_for_myle_app_state()
        if self.is_login_page():
            self.login_to_myle()
            self._wait_for_myle_app_state()
        self.state.active_url = page.url

    @staticmethod
    def _calendar_url() -> str:
        return f"{EMR_BASE_URL.rstrip('/')}/calendar"

    @staticmethod
    def _normalize_patient_text(value: str) -> str:
        return " ".join(value.lower().replace(",", " ").split())

    @staticmethod
    def _looks_like_identifier(value: str) -> bool:
        digits = re.sub(r"\D", "", value)
        return len(digits) >= 8

    @staticmethod
    def _name_query_matches_row(query: str, row_text: str) -> bool:
        normalized_query = PlaywrightHarness._normalize_patient_text(query)
        normalized_row = PlaywrightHarness._normalize_patient_text(row_text)
        if not normalized_query:
            return False
        if normalized_query in normalized_row:
            return True

        query_tokens = [token for token in normalized_query.split() if len(token) > 1]
        row_tokens = set(normalized_row.split())
        if not query_tokens:
            return False

        return all(any(token == row_token or row_token.startswith(token) for row_token in row_tokens) for token in query_tokens)

    def go_to_myle_calendar(self) -> None:
        self.ensure_myle_ready()
        if not self.current_url().lower().rstrip("/").endswith("/calendar"):
            self.page.goto(self._calendar_url(), wait_until="domcontentloaded")
            self._wait_for_myle_app_state()
        self.state.active_url = self.page.url

    def bind_patient_from_calendar(self, patient_query: str) -> None:
        query = patient_query.strip()
        if not query:
            raise RuntimeError("Patient query is required for patient binding.")

        self.go_to_myle_calendar()
        page = self.page

        search = page.locator("input[placeholder='Search']").first
        search.wait_for(state="visible", timeout=10000)
        search.fill("")
        search.fill(query)
        page.wait_for_timeout(1500)

        rows = page.locator("[data-cy='sidebar-patients-div'] [data-cy^='sidebar-patient-']")
        row_count = rows.count()
        if row_count == 0:
            raise RuntimeError(f"No patient results were visible for query '{query}'.")

        is_identifier_query = self._looks_like_identifier(query)
        identifier_digits = re.sub(r"\D", "", query)

        matches = []
        for i in range(row_count):
            row = rows.nth(i)
            if not row.is_visible():
                continue
            row_text = row.inner_text()
            normalized_row_text = self._normalize_patient_text(row_text)
            row_digits = re.sub(r"\D", "", row_text)

            if is_identifier_query:
                if identifier_digits and identifier_digits in row_digits:
                    matches.append(row)
            else:
                if self._name_query_matches_row(query, row_text):
                    matches.append(row)

        if not matches:
            raise RuntimeError(f"No matching patient row was found for query '{query}'.")
        if len(matches) > 1:
            raise RuntimeError(f"Patient query '{query}' is ambiguous across {len(matches)} visible results.")

        result_name = matches[0].locator(".tbc span").first
        result_name.wait_for(state="visible", timeout=10000)
        result_name.click()
        page.wait_for_timeout(2500)

        self.state.active_url = page.url
        self.state.active_patient_query = query

    def open_current_patient_documents(self) -> None:
        page = self.page
        documents_tab = page.locator("[data-cy='patientTab-documents']").first
        documents_tab.wait_for(state="visible", timeout=10000)
        documents_tab.click()
        self._wait_for_myle_app_state()
        page.wait_for_timeout(2000)
        self.state.active_url = page.url

    def open_current_patient_results(self) -> None:
        page = self.page
        results_tab = page.locator("[data-cy='patientTab-results']").first
        results_tab.wait_for(state="visible", timeout=10000)
        results_tab.click()
        self._wait_for_myle_app_state()
        page.wait_for_timeout(2000)
        self.state.active_url = page.url

    def return_to_current_patient_home(self) -> None:
        page = self.page
        selectors = (
            "[data-cy='patientTab-home']",
            "[data-cy='patientTab-summary']",
            "[data-cy='patientTab-overview']",
            "[data-cy='patientTab-patient']",
        )
        for selector in selectors:
            locator = page.locator(selector).first
            if locator.count() > 0 and locator.is_visible():
                locator.click()
                self._wait_for_myle_app_state()
                page.wait_for_timeout(1500)
                self.state.active_url = page.url
                return
        raise RuntimeError("Could not find a chart-home control to restore patient home surface.")

    def restore_surface_for_resume(self, target_surface: SurfaceType) -> bool:
        try:
            self.ensure_myle_ready()
            if target_surface == SurfaceType.DOCUMENTS:
                self.open_current_patient_documents()
                return True
            if target_surface == SurfaceType.RESULTS:
                self.open_current_patient_results()
                return True
            if target_surface == SurfaceType.CHART_HOME:
                self.return_to_current_patient_home()
                return True
        except Exception:
            return False
        return False

    def snapshot_actionable_elements(self) -> list[dict[str, str]]:
        page = self.page
        page.bring_to_front()
        elements = page.evaluate(
            """
            () => {
              const candidates = Array.from(document.querySelectorAll(
                "a, button, input, textarea, select, [role='button'], [data-cy], .pointer, .sidebar-item, tbody.myle-table-row, td.pointer"
              ));
              let counter = 0;
              const visible = [];
              for (const el of candidates) {
                const rect = el.getBoundingClientRect();
                const style = window.getComputedStyle(el);
                const isVisible = rect.width > 0 && rect.height > 0 &&
                  style.visibility !== "hidden" && style.display !== "none";
                if (!isVisible) continue;
                const text = (el.innerText || el.textContent || "").replace(/\\s+/g, " ").trim();
                const title = (el.getAttribute("title") || "").trim();
                const placeholder = (el.getAttribute("placeholder") || "").trim();
                const dataCy = (el.getAttribute("data-cy") || "").trim();
                const type = (el.getAttribute("type") || "").trim();
                const tag = el.tagName.toLowerCase();
                const label = [dataCy, title, placeholder, text].filter(Boolean).join(" | ").slice(0, 220);
                if (!label) continue;
                const agentId = `a${counter++}`;
                el.setAttribute("data-agent-id", agentId);
                visible.push({
                  agent_id: agentId,
                  tag,
                  type,
                  label,
                  text: text.slice(0, 220),
                  data_cy: dataCy,
                  title,
                  placeholder,
                });
              }
              return visible;
            }
            """
        )
        return elements

    def click_agent_target(self, agent_id: str) -> None:
        target = self.page.locator(f"[data-agent-id='{agent_id}']").first
        target.wait_for(state="visible", timeout=10000)
        target.click()
        self._wait_for_myle_app_state()
        self.page.wait_for_timeout(1500)
        self.state.active_url = self.page.url

    def type_agent_target(self, agent_id: str, text: str) -> None:
        target = self.page.locator(f"[data-agent-id='{agent_id}']").first
        target.wait_for(state="visible", timeout=10000)
        target.fill("")
        target.fill(text)
        self.page.wait_for_timeout(1200)
        self.state.active_url = self.page.url

    def scroll_page(self, direction: str) -> None:
        delta = 900 if direction == "down" else -900
        self.page.mouse.wheel(0, delta)
        self.page.wait_for_timeout(1200)
        self.state.active_url = self.page.url

    def login_to_myle(self) -> None:
        if not self.is_login_page():
            raise RuntimeError("Refusing to type credentials because the page is not the validated Myle login page.")
        if not MYLE_USERNAME or not MYLE_PASSWORD:
            raise RuntimeError("MYLE_USERNAME or MYLE_PASSWORD is not set in the environment.")

        page = self.page
        page.bring_to_front()
        page.fill(MYLE_LOGIN_USERNAME_SELECTOR, MYLE_USERNAME)
        page.fill(MYLE_LOGIN_PASSWORD_SELECTOR, MYLE_PASSWORD)
        page.click(MYLE_LOGIN_BUTTON_SELECTOR)
        page.wait_for_timeout(3000)
        self.state.active_url = page.url

    def capture_screenshot(self, path: Path) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        self.page.screenshot(path=str(path), full_page=True)
        return path

    def close(self) -> None:
        # Keep the dedicated browser profile alive across runs; only disconnect Playwright.
        with suppress(Exception):
            if self._playwright is not None:
                self._playwright.stop()
        self._context = None
        self._browser = None
        self._page = None
        self._playwright = None
        self.state.browser_connected = False
