import logging
import asyncio
import json
from typing import List, Dict, Any
from pathlib import Path

from playwright.async_api import Page, Route

from src.core.hive_mind import HiveMind
from src.core.session_manager import SessionManager

logger = logging.getLogger(__name__)

class PostCollectorTask:
    """
    A task to collect all posts for users with 'profile_collected' status
    and update their status to 'posts_collected'.
    """

    def __init__(self, session_manager: SessionManager, hive_mind: HiveMind):
        self.session = session_manager
        self.hive_mind = hive_mind
        self.collected_posts: Dict[str, List[Any]] = {}

    async def _handle_feed_route(self, route: Route, user_did: str):
        """
        Intercepts the 'getAuthorFeed' API request and captures the post data
        from the JSON response.
        """
        try:
            response = await route.fetch()
            json_data = await response.json()
            
            if "feed" in json_data:
                if user_did not in self.collected_posts:
                    self.collected_posts[user_did] = []
                
                posts = json_data["feed"]
                self.collected_posts[user_did].extend(posts)
                logger.debug(f"Captured {len(posts)} posts for user {user_did}")
            
            await route.fulfill(response=response)
        except Exception as e:
            logger.error(f"Error processing 'getAuthorFeed' route: {e}")
            await route.continue_()

    async def run(self):
        """
        Fetches 'profile_collected' users from the Hive Mind, collects their posts,
        and updates their status.
        """
        logger.info("Starting post collector task...")
        users_to_process = self.hive_mind.get_users_by_status("profile_collected", limit=5)

        if not users_to_process:
            logger.info("No users with collected profiles to process.")
            return

        logger.info(f"Found {len(users_to_process)} users to collect posts for.")

        context = await self.session.get_context()

        async def collect_posts(user_did: str):
            page = await context.new_page()
            try:
                self.collected_posts[user_did] = []

                await page.route(
                    "**/xrpc/app.bsky.feed.getAuthorFeed",
                    lambda route: self._handle_feed_route(route, user_did)
                )

                url = f"https://bsky.app/profile/{user_did}"
                logger.info(f"Navigating to profile for post collection: {url}")
                await page.goto(url, wait_until="networkidle")

                # Scroll to capture the feed
                for _ in range(5): # Scroll a few times to get more posts
                    await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    await asyncio.sleep(1)

                await page.unroute("**/xrpc/app.bsky.feed.getAuthorFeed")

                if self.collected_posts.get(user_did):
                    # Save the raw data to the staging area
                    staging_path = Path("data/staging/posts")
                    staging_path.mkdir(exist_ok=True, parents=True)
                    with open(staging_path / f"{user_did}_posts.jsonl", "a") as f:
                        for post in self.collected_posts[user_did]:
                            f.write(json.dumps(post) + "\n")
                            
                    logger.info(f"Collected {len(self.collected_posts[user_did])} posts for {user_did}.")
                    self.hive_mind.update_user_status(user_did, "posts_collected")
                else:
                    logger.warning(f"No posts were collected for {user_did}.")
            finally:
                await page.close()

        tasks = [collect_posts(did) for did in users_to_process]
        await asyncio.gather(*tasks)

        logger.info("Post collector task finished.")