"""Login macro player — executes steps to authenticate before scan."""
import logging
import re
import time
from typing import Dict, List, Optional

from modules.login_replay.macro import MacroError

logger = logging.getLogger(__name__)


def _substitute(template: str, vars_: Dict[str, str]) -> str:
    """Replace ${name} with vars_[name]. Missing vars become empty string."""
    if not isinstance(template, str):
        return template

    def replace(match):
        return str(vars_.get(match.group(1), ""))

    return re.sub(r"\$\{(\w+)\}", replace, template)


def _substitute_recursive(value, vars_: Dict[str, str]):
    """Recurse through dict/list, substituting strings."""
    if isinstance(value, str):
        return _substitute(value, vars_)
    if isinstance(value, dict):
        return {k: _substitute_recursive(v, vars_) for k, v in value.items()}
    if isinstance(value, list):
        return [_substitute_recursive(v, vars_) for v in value]
    return value


def extract_csrf_value(html: str, selector: str) -> Optional[str]:
    """Pull `value` attribute from element matched by simple selector."""
    if not html:
        return None

    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "html.parser")
        el = soup.select_one(selector)
        if el and el.has_attr("value"):
            return el["value"]
    except ImportError:
        pass

    name_match = re.match(r"input\[name=[\"']?([\w-]+)[\"']?\]", selector)
    if name_match:
        name = name_match.group(1)
        pattern = re.compile(
            rf'<input[^>]+name=["\']?{re.escape(name)}["\']?[^>]+value=["\']([^"\']+)["\']',
            re.IGNORECASE,
        )
        match = pattern.search(html)
        if match:
            return match.group(1)
        pattern2 = re.compile(
            rf'<input[^>]+value=["\']([^"\']+)["\'][^>]+name=["\']?{re.escape(name)}["\']?',
            re.IGNORECASE,
        )
        match2 = pattern2.search(html)
        if match2:
            return match2.group(1)
    return None


class LoginPlayer:
    """Execute a login macro using an http_client to authenticate."""

    def __init__(self, http_client, config: Optional[Dict] = None):
        self.http_client = http_client
        config = config or {}
        lr_cfg = config.get("login_replay", {}) if isinstance(config.get("login_replay"), dict) else {}
        self.abort_on_fail = bool(lr_cfg.get("abort_on_fail", True))
        self._authenticated = False
        self._last_response_text = ""

    def is_authenticated(self) -> bool:
        return self._authenticated

    def play(self, macro: Dict) -> bool:
        """Execute macro steps, then run auth_check. Returns True on success."""
        vars_: Dict[str, str] = {}
        steps: List[Dict] = macro.get("steps", [])

        for i, step in enumerate(steps):
            action = step.get("action")
            try:
                step_resolved = _substitute_recursive(step, vars_)
                self._execute_step(action, step_resolved, vars_, step_index=i)
            except Exception as e:
                logger.error(f"Login replay step {i} ({action}) failed: {e}")
                self._authenticated = False
                return False

        auth_check = macro.get("auth_check")
        if auth_check:
            ok = self._run_auth_check(auth_check)
            self._authenticated = ok
            return ok

        self._authenticated = True
        return True

    def _execute_step(self, action: str, step: Dict, vars_: Dict, step_index: int) -> None:
        if action == "get":
            response = self.http_client.get(step["url"], headers=step.get("headers"))
            self._last_response_text = self._response_text(response)
            self._check_expectations(step, response)

        elif action == "post":
            response = self.http_client.post(
                step["url"],
                data=step.get("data", {}),
                headers=step.get("headers"),
            )
            self._last_response_text = self._response_text(response)
            self._check_expectations(step, response)

        elif action == "extract_csrf":
            selector = step.get("from", "")
            save_as = step.get("save_as", "csrf")
            value = extract_csrf_value(self._last_response_text, selector)
            if value is None:
                logger.warning(f"Step {step_index}: CSRF extraction failed for {selector}")
                vars_[save_as] = ""
            else:
                vars_[save_as] = value

        elif action == "extract_header":
            save_as = step.get("save_as", "header")
            vars_[save_as] = ""

        elif action == "set_cookie":
            name = step.get("name", "")
            value = step.get("value", "")
            domain = step.get("domain", None)
            if hasattr(self.http_client, "session"):
                self.http_client.session.cookies.set(name, value, domain=domain)

        elif action == "wait":
            time.sleep(float(step.get("seconds", 1)))

        elif action == "playwright":
            url = step.get("url") or step.get("goto")
            if not url:
                logger.warning(f"Step {step_index}: playwright action missing url/goto")
                return
            try:
                from playwright.sync_api import sync_playwright
            except ImportError:
                logger.warning(
                    f"Step {step_index}: playwright not installed "
                    "(pip install playwright && playwright install chromium)"
                )
                return
            headless = step.get("headless", True)
            wait_ms = int(step.get("wait_ms", 2000))
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=headless)
                page = browser.new_page()
                page.goto(url, wait_until="domcontentloaded")
                for click_sel in step.get("clicks", []) or []:
                    page.click(click_sel)
                for fill in step.get("fills", []) or []:
                    page.fill(fill.get("selector", ""), fill.get("value", ""))
                if step.get("submit"):
                    page.click(step["submit"])
                page.wait_for_timeout(wait_ms)
                self._last_response_text = page.content()
                if hasattr(self.http_client, "session"):
                    for c in page.context.cookies():
                        self.http_client.session.cookies.set(
                            c.get("name", ""),
                            c.get("value", ""),
                            domain=c.get("domain"),
                            path=c.get("path", "/"),
                        )
                browser.close()

        else:
            raise MacroError(f"Unknown action: {action}")

    def _response_text(self, response) -> str:
        if response is None:
            return ""
        if hasattr(response, "text"):
            text = response.text
            return text if isinstance(text, str) else (text() if callable(text) else "")
        if hasattr(response, "content"):
            content = response.content
            if isinstance(content, bytes):
                try:
                    return content.decode("utf-8", errors="replace")
                except Exception:
                    return ""
        return ""

    def _check_expectations(self, step: Dict, response) -> None:
        expect_status = step.get("expect_status")
        if expect_status:
            status = getattr(response, "status_code", None)
            if status not in expect_status:
                raise MacroError(f"Status {status} not in expected {expect_status}")
        expect_contains = step.get("expect_contains")
        if expect_contains:
            text = self._response_text(response)
            if expect_contains not in text:
                raise MacroError(f"Response does not contain '{expect_contains}'")

    def _run_auth_check(self, auth_check: Dict) -> bool:
        try:
            response = self.http_client.get(auth_check.get("url", ""))
            text = self._response_text(response)
            must_contain = auth_check.get("must_contain")
            must_not_contain = auth_check.get("must_not_contain")

            if must_contain and must_contain not in text:
                logger.error(f"Auth check failed: missing '{must_contain}'")
                return False
            if must_not_contain and must_not_contain in text:
                logger.error(f"Auth check failed: '{must_not_contain}' present")
                return False
            return True
        except Exception as e:
            logger.error(f"Auth check exception: {e}")
            return False
