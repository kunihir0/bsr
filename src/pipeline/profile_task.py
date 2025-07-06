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

    async def _handle_profile_route(self, route: Route):
        """
        Intercepts the 'getProfile' API request and captures the user profile
        from the JSON response.
        """
        try:
            response = await route.fetch()
            json_data = await response.json()
            
            did = json_data.get("did")
            if did:
                self.collected_profiles[did] = json_data
                logger.debug(f"Captured profile for user {did}")

            await route.fulfill(response=response)
        except Exception as e:
            logger.error(f"Error processing 'getProfile' route: {e}")
            await route.continue_()

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
                await page.route(
                    "**/xrpc/app.bsky.actor.getProfile",
                    self._handle_profile_route
                )
                url = f"https://bsky.app/profile/{user_did}"
                logger.info(f"Navigating to profile: {url}")
                await page.goto(url, wait_until="networkidle")
                await asyncio.sleep(2)

                if user_did in self.collected_profiles:
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