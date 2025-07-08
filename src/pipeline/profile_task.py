import logging
import asyncio
import json
from typing import Dict, Any
from pathlib import Path

from playwright.async_api import Page, Route

from src.core.hive_mind import HiveMind
from src.core.session_manager import SessionManager
from src.models.models import BlueSkyUser

logger = logging.getLogger(__name__)

class ProfileCollectorTask:
    """
    A task to collect detailed profile information for users in the Hive Mind
    and update their status.
    """

    def __init__(self, session_manager: SessionManager, hive_mind: HiveMind):
        self.session = session_manager
        self.hive_mind = hive_mind
        self.collected_profiles: Dict[str, Any] = {}

    async def _scrape_profile(self, page: Page) -> Dict[str, Any]:
        """Scrapes profile data from a user's profile page."""
        profile = {}
        try:
            profile['displayName'] = await page.locator('[data-testid="profileHeaderDisplayName"]').inner_text()
            profile['handle'] = await page.locator('[data-testid="profileHeaderHandle"]').inner_text()
            profile['followersCount'] = await page.locator('[data-testid="profileHeaderFollowersButton"]').inner_text()
            profile['followsCount'] = await page.locator('[data-testid="profileHeaderFollowsButton"]').inner_text()
            profile['description'] = await page.locator('[data-testid="profileHeaderDescription"]').inner_text()
            
            # Extract numbers from counts
            profile['followersCount'] = int(''.join(filter(str.isdigit, profile['followersCount'])))
            profile['followsCount'] = int(''.join(filter(str.isdigit, profile['followsCount'])))

        except Exception as e:
            logger.error(f"Error scraping profile: {e}")
        return profile

    async def run(self):
        """
        Fetches 'queued' users from the Hive Mind, collects their profiles,
        and updates their status.
        """
        logger.info("Starting profile collector task...")
        queued_users = self.hive_mind.get_users_by_status("queued", limit=10) # Process 10 at a time

        if not queued_users:
            logger.info("No queued users to process.")
            return

        logger.info(f"Found {len(queued_users)} users to process.")
        
        context = await self.session.get_context()

        async def collect_profile(user_did: str):
            page = await context.new_page()
            try:
                url = f"https://bsky.app/profile/{user_did}"
                logger.info(f"Navigating to profile: {url}")
                await page.goto(url, wait_until="networkidle")
                
                profile_data = await self._scrape_profile(page)
                if profile_data:
                    self.collected_profiles[user_did] = profile_data
                    
                    # Save the raw data to the staging area
                    staging_path = Path("data/staging/profiles")
                    staging_path.mkdir(exist_ok=True, parents=True)
                    with open(staging_path / f"{user_did}.json", "w") as f:
                        json.dump(self.collected_profiles[user_did], f)

                    logger.info(f"Successfully collected profile for {user_did}.")
                    self.hive_mind.update_user_status(user_did, "profile_collected")
                else:
                    logger.warning(f"Failed to collect profile for {user_did}.")
            finally:
                await page.close()

        tasks = [collect_profile(did) for did in queued_users]
        await asyncio.gather(*tasks)
        
        logger.info("Profile collector task finished.")