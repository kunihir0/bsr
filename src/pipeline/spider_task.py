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

    async def _handle_follows_route(self, route: Route):
        """
        Intercepts the 'getFollows' API request and captures the user data
        from the JSON response.
        """
        try:
            response = await route.fetch()
            json_data = await response.json()
            
            if "follows" in json_data and isinstance(json_data["follows"], list):
                # Save the raw data to the staging area
                staging_path = Path("data/staging/follows")
                staging_path.mkdir(exist_ok=True, parents=True)
                
                # Use the 'subject' DID if available, otherwise use a generic name
                subject_did = json_data.get("subject", {}).get("did", "unknown_user")
                
                with open(staging_path / f"{subject_did}_follows.jsonl", "a") as f:
                    for user in json_data["follows"]:
                        f.write(json.dumps(user) + "\n")

                for user in json_data["follows"]:
                    if isinstance(user, dict) and "did" in user:
                        did = user.get("did")
                        if did and did not in self.discovered_users:
                            self.discovered_users.append(did)
                            logger.debug(f"Discovered user via network interception: {did}")
            
            # Fulfill the request to let the page load normally
            await route.fulfill(response=response)
        except Exception as e:
            logger.error(f"Error processing 'getFollows' route: {e}")
            await route.continue_()

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
            # Set up network interception
            await page.route(
                "**/xrpc/app.bsky.graph.getFollows",
                self._handle_follows_route
            )

            # Navigate to the user's 'following' page
            url = f"https://bsky.app/profile/{seed_user_handle}/follows"
            logger.info(f"Navigating to {url}")
            await page.goto(url, wait_until="networkidle")

            # Scroll down to load more users
            for _ in range(10): # Scroll 10 times to get a good number of users
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await asyncio.sleep(1)

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