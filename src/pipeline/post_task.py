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

    async def _scrape_posts(self, page: Page, user_did: str):
        """Scrapes posts from a user's profile page."""
        posts = []
        post_elements = await page.locator('[data-testid^="postThreadItem-by-"]').all()
        for post_el in post_elements:
            try:
                post_text_element = await post_el.query_selector('div[data-word-wrap="1"]')
                post_text = await post_text_element.inner_text() if post_text_element else ""

                reply_count_element = await post_el.query_selector('[data-testid="replyCount"]')
                reply_count = await reply_count_element.inner_text() if reply_count_element else "0"
                
                repost_count_element = await post_el.query_selector('[data-testid="repostCount"]')
                repost_count = await repost_count_element.inner_text() if repost_count_element else "0"

                like_count_element = await post_el.query_selector('[data-testid="likeCount"]')
                like_count = await like_count_element.inner_text() if like_count_element else "0"

                post_link_element = await post_el.query_selector('a[href*="/post/"]')
                post_uri = await post_link_element.get_attribute('href') if post_link_element else ""


                posts.append({
                    "uri": post_uri,
                    "text": post_text,
                    "replyCount": int(reply_count),
                    "repostCount": int(repost_count),
                    "likeCount": int(like_count),
                })
            except Exception as e:
                logger.error(f"Error scraping a post for {user_did}: {e}")
        
        return posts
    
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
                url = f"https://bsky.app/profile/{user_did}"
                logger.info(f"Navigating to profile for post collection: {url}")
                await page.goto(url, wait_until="networkidle")

                # Scroll to load all posts
                last_height = await page.evaluate("document.body.scrollHeight")
                while True:
                    await page.mouse.wheel(0, 15000)
                    await asyncio.sleep(2)  # Wait for new posts to load
                    new_height = await page.evaluate("document.body.scrollHeight")
                    if new_height == last_height:
                        break
                    last_height = new_height

                scraped_posts = await self._scrape_posts(page, user_did)
                self.collected_posts[user_did] = scraped_posts

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