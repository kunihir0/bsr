import logging
import asyncio
import json
from typing import List
from pathlib import Path

from playwright.async_api import Page, Route

from src.core.hive_mind import HiveMind
from src.core.session_manager import SessionManager

logger = logging.getLogger(__name__)

class SpiderTask:
    """
    A task responsible for discovering new user handles by spidering through
    'following' lists and adding them to the Hive Mind.
    """

    def __init__(self, session_manager: SessionManager, hive_mind: HiveMind):
        self.session = session_manager
        self.hive_mind = hive_mind
        self.discovered_users: List[str] = []

    async def _scrape_followers(self, page: Page) -> List[str]:
        """Scrapes followers from a user's profile page."""
        dids = []
        user_links = await page.locator('a[href*="/profile/did:plc:"]').all()
        for link in user_links:
            href = await link.get_attribute('href')
            if href:
                did = href.split('/')[-1]
                if did.startswith('did:plc:'):
                    dids.append(did)
        return list(set(dids)) # Return unique dids

    async def run(self, seed_user_handle: str):
        """
        Starts the spidering process from a given seed user.

        Args:
            seed_user_handle: The handle of the user to start spidering from.
        """
        logger.info(f"Starting spider task for seed user: {seed_user_handle}")
        context = await self.session.get_context()
        page = await context.new_page()

        try:
            # Navigate to the user's 'following' page
            url = f"https://bsky.app/profile/{seed_user_handle}/follows"
            logger.info(f"Navigating to {url}")
            await page.goto(url, wait_until="networkidle")

            # Scroll down to load more users
            last_height = await page.evaluate("document.body.scrollHeight")
            while True:
                await page.mouse.wheel(0, 15000)
                await asyncio.sleep(2)  # Wait for new users to load
                new_height = await page.evaluate("document.body.scrollHeight")
                if new_height == last_height:
                    break
                last_height = new_height

            discovered_dids = await self._scrape_followers(page)
            self.discovered_users.extend(discovered_dids)
            
            logger.info(f"Finished spidering. Found {len(self.discovered_users)} unique users.")

            # Add discovered users to the Hive Mind
            for did in self.discovered_users:
                if not self.hive_mind.get_user_status(did):
                    self.hive_mind.add_user(did, status="queued")
                else:
                    logger.debug(f"User {did} already exists in Hive Mind. Skipping.")

        except Exception as e:
            logger.error(f"An error occurred during the spider task: {e}")
        finally:
            await page.close()