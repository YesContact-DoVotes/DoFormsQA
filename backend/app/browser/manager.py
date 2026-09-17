import asyncio
import os
import time
from pathlib import Path
from typing import Dict, Any, List, Optional
from playwright.async_api import async_playwright, Browser, BrowserContext, Page, ConsoleMessage, Response
from loguru import logger
from backend.app.config import settings
from backend.app.browser.dom_snapshot import DOMSnapshot, EXTRACT_DOM_JS


class BrowserManager:
    def __init__(self, headless: bool = False, session_storage_dir: Optional[Path] = None):
        self.headless = headless
        self.session_storage_dir = session_storage_dir or settings.STORAGE_PATH
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None

        self.console_logs: List[Dict[str, Any]] = []
        self.network_errors: List[Dict[str, Any]] = []
        self._action_history: List[str] = []

    async def initialize(self):
        """Launches Chromium browser and sets up listeners."""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=self.headless,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
            ]
        )
        self.context = await self.browser.new_context(
            viewport={
                "width": settings.BROWSER_VIEWPORT_WIDTH,
                "height": settings.BROWSER_VIEWPORT_HEIGHT
            },
            ignore_https_errors=True
        )
        self.page = await self.context.new_page()

        # Set standard timeouts
        self.page.set_default_timeout(settings.ACTION_TIMEOUT_MS)

        # Listeners for console logs
        self.page.on("console", self._handle_console)
        self.page.on("pageerror", self._handle_pageerror)
        self.page.on("response", self._handle_response)

    def _handle_console(self, msg: ConsoleMessage):
        log_entry = {
            "type": msg.type,
            "text": msg.text,
            "location": msg.location,
            "timestamp": time.time()
        }
        self.console_logs.append(log_entry)
        if msg.type in ["error", "warning"]:
            logger.debug("[Browser Console {}] {}", msg.type.upper(), msg.text)

    def _handle_pageerror(self, exc):
        log_entry = {
            "type": "pageerror",
            "text": str(exc),
            "timestamp": time.time()
        }
        self.console_logs.append(log_entry)
        logger.warning("[Browser Unhandled Error] {}", exc)

    def _handle_response(self, response: Response):
        if response.status >= 400:
            self.network_errors.append({
                "url": response.url,
                "status": response.status,
                "status_text": response.status_text,
                "method": response.request.method,
                "timestamp": time.time()
            })
            logger.warning("[Browser Network Error] {} {} -> HTTP {}", response.request.method, response.url, response.status)

    async def navigate(self, url: str) -> Dict[str, Any]:
        """Navigates to the specified URL."""
        if not self.page:
            raise RuntimeError("Browser not initialized")
        
        start_time = time.time()
        try:
            logger.debug("[Browser] Navigating to '{}'...", url)
            await self.page.goto(url, wait_until="domcontentloaded", timeout=15000)
            await asyncio.sleep(0.5)  # allow dynamic content to stabilize
            duration_ms = (time.time() - start_time) * 1000
            return {"status": "success", "url": self.page.url, "duration_ms": duration_ms}
        except Exception as e:
            logger.error("[Browser] Failed navigating to '{}': {}", url, e)
            return {"status": "error", "error": str(e), "url": url}


    async def execute_action(self, action: str, target: Optional[str] = None, value: Optional[str] = None) -> Dict[str, Any]:
        """
        Executes an atomic browser action with robust fallback heuristics.
        Supported actions:
        - navigate (target=url)
        - click (target=selector or text)
        - fill / type (target=selector, value=text)
        - select (target=selector, value=option_value_or_text)
        - check (target=selector)
        - uncheck (target=selector)
        - press_key (value=key like 'Enter', 'Tab', 'Escape')
        - scroll (value='down', 'up')
        - back
        - forward
        - reload
        - wait (value=seconds or milliseconds)
        """
        if not self.page:
            raise RuntimeError("Browser not initialized")

        start_time = time.time()
        action_name = action.lower().strip()
        error_msg = None

        try:
            if action_name == "navigate":
                await self.page.goto(target or value, wait_until="domcontentloaded", timeout=15000)
                await asyncio.sleep(0.5)

            elif action_name == "click":
                element = await self._find_element(target)
                if element:
                    await element.scroll_into_view_if_needed()
                    await element.click(timeout=settings.ACTION_TIMEOUT_MS)
                else:
                    raise ValueError(f"Could not locate element to click with target: {target}")

            elif action_name in ["fill", "type", "input"]:
                element = await self._find_element(target)
                if element:
                    await element.scroll_into_view_if_needed()
                    await element.fill(value or "")
                else:
                    raise ValueError(f"Could not locate input element with target: {target}")

            elif action_name == "select":
                element = await self._find_element(target)
                if element:
                    await element.select_option(value=value or "")
                else:
                    raise ValueError(f"Could not locate select element with target: {target}")

            elif action_name == "check":
                element = await self._find_element(target)
                if element:
                    await element.check()
                else:
                    raise ValueError(f"Could not locate checkbox with target: {target}")

            elif action_name == "uncheck":
                element = await self._find_element(target)
                if element:
                    await element.uncheck()
                else:
                    raise ValueError(f"Could not locate checkbox with target: {target}")

            elif action_name in ["press", "press_key", "key"]:
                key = value or target or "Enter"
                await self.page.keyboard.press(key)

            elif action_name == "scroll":
                direction = (value or target or "down").lower()
                delta = 400 if direction == "down" else -400
                await self.page.mouse.wheel(0, delta)
                await asyncio.sleep(0.3)

            elif action_name == "back":
                await self.page.go_back(wait_until="domcontentloaded")

            elif action_name == "forward":
                await self.page.go_forward(wait_until="domcontentloaded")

            elif action_name == "reload":
                await self.page.reload(wait_until="domcontentloaded")
                await asyncio.sleep(0.5)

            elif action_name == "wait":
                wait_sec = float(value or 1.0)
                if wait_sec > 5.0:
                    wait_sec = 5.0
                await asyncio.sleep(wait_sec)

            else:
                raise ValueError(f"Unsupported browser action: {action_name}")

            await asyncio.sleep(0.3)  # stabilize UI after action
            duration_ms = (time.time() - start_time) * 1000
            return {
                "status": "success",
                "action": action_name,
                "target": target,
                "value": value,
                "url": self.page.url,
                "duration_ms": duration_ms
            }

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            error_msg = str(e)
            return {
                "status": "error",
                "action": action_name,
                "target": target,
                "value": value,
                "url": self.page.url if self.page else "",
                "error": error_msg,
                "duration_ms": duration_ms
            }

    async def _find_element(self, target: Optional[str]):
        """Locates an element using CSS selector, role selector, text selector or heuristics."""
        if not target or not self.page:
            return None

        target = target.strip()

        # 1. Direct CSS / testid / id selector
        if target.startswith("#") or target.startswith("[") or target.startswith("."):
            try:
                el = await self.page.query_selector(target)
                if el:
                    return el
            except Exception:
                pass

        # 2. Try exact text or substring text with Playwright locator
        try:
            # Button with exact text or regex
            btn = self.page.get_by_role("button", name=target)
            if await btn.count() > 0:
                return btn.first
        except Exception:
            pass

        try:
            # Link with text
            link = self.page.get_by_role("link", name=target)
            if await link.count() > 0:
                return link.first
        except Exception:
            pass

        try:
            # Placeholder or Label for input
            input_by_ph = self.page.get_by_placeholder(target)
            if await input_by_ph.count() > 0:
                return input_by_ph.first
            input_by_lbl = self.page.get_by_label(target)
            if await input_by_lbl.count() > 0:
                return input_by_lbl.first
        except Exception:
            pass

        try:
            # General text
            text_el = self.page.get_by_text(target, exact=False)
            if await text_el.count() > 0:
                return text_el.first
        except Exception:
            pass

        # 3. Fallback query selector
        try:
            return await self.page.query_selector(target)
        except Exception:
            return None

    async def get_state(self) -> Dict[str, Any]:
        """Returns snapshot, URL, title, recent console logs and network errors."""
        if not self.page or self.page.is_closed():
            return {
                "url": "",
                "title": "",
                "formatted_dom": "Browser not initialized or closed",
                "raw_dom": {},
                "console_errors": [],
                "network_errors": []
            }

        try:
            raw_snapshot = await self.page.evaluate(EXTRACT_DOM_JS)
        except Exception as e:
            page_url = ""
            page_title = ""
            try:
                if self.page and not self.page.is_closed():
                    page_url = self.page.url
                    page_title = await self.page.title()
            except Exception:
                pass

            raw_snapshot = {
                "url": page_url,
                "title": page_title,
                "interactiveElements": [],
                "textExcerpt": f"Error extracting DOM: {e}"
            }

        formatted_dom = DOMSnapshot.format_for_llm(raw_snapshot)

        # Extract only error/warning logs for context
        relevant_console_errors = [
            log for log in self.console_logs
            if log.get("type") in ["error", "pageerror"]
        ][-10:]

        relevant_network_errors = self.network_errors[-10:]

        page_url = ""
        try:
            if self.page and not self.page.is_closed():
                page_url = self.page.url
        except Exception:
            pass

        return {
            "url": page_url or raw_snapshot.get("url", ""),
            "title": raw_snapshot.get("title", ""),
            "formatted_dom": formatted_dom,
            "raw_dom": raw_snapshot,
            "console_errors": relevant_console_errors,
            "network_errors": relevant_network_errors
        }

    async def take_screenshot(self, save_path: Path) -> str:
        """Takes a full page screenshot and returns the file path."""
        if not self.page:
            raise RuntimeError("Browser not initialized")

        save_path.parent.mkdir(parents=True, exist_ok=True)
        await self.page.screenshot(path=str(save_path), full_page=True)
        return str(save_path)

    async def clear_state(self):
        """Clears console logs and network error buffers."""
        self.console_logs.clear()
        self.network_errors.clear()

    async def close(self):
        """Safely closes page, context, browser and stops Playwright."""
        try:
            if self.page:
                await self.page.close()
        except Exception:
            pass
        try:
            if self.context:
                await self.context.close()
        except Exception:
            pass
        try:
            if self.browser:
                await self.browser.close()
        except Exception:
            pass
        try:
            if self.playwright:
                await self.playwright.stop()
        except Exception:
            pass
