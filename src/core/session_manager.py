import logging
from pathlib import Path
from typing import Optional

from playwright.async_api import async_playwright, Browser, BrowserContext, Playwright

logger = logging.getLogger(__name__)

class SessionManager:
    """
    Manages the Playwright browser session, including loading and saving session state.
    """

    def __init__(self, session_file: Path = Path("session.json")):
        self.session_file = session_file
        self.playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None

    async def __aenter__(self):
        """Initializes the Playwright session."""
        logger.info("Starting Playwright session...")
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=False)
        
        logger.info("Creating a new browser context.")
        self.context = await self.browser.new_context()
            
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Closes the Playwright session."""
        if self.context:
            logger.info(f"Saving session to '{self.session_file}'...")
            await self.context.storage_state(path=self.session_file)
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        logger.info("Playwright session closed.")

    async def get_context(self) -> BrowserContext:
        """Returns the current browser context."""
        if not self.context:
            raise ConnectionError("Session has not been initialized. Call __aenter__ first.")
        return self.context