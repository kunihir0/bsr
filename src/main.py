import logging
import time
import asyncio
from datetime import datetime

import typer
from rich.console import Console
from rich.live import Live
from rich.logging import RichHandler
from rich.panel import Panel
from rich.table import Table

from src.core.logger_config import setup_logger
from src.core.session_manager import SessionManager
from src.core.hive_mind import HiveMind
from src.pipeline.spider_task import SpiderTask
from src.pipeline.profile_task import ProfileCollectorTask
from src.pipeline.post_task import PostCollectorTask

# Setup logger
setup_logger()
logger = logging.getLogger(__name__)

def generate_layout() -> Panel:
    """Defines the overall layout of the terminal UI."""
    worker_table = Table(
        title="Worker Status",
        caption="Live status of all scraper workers",
        expand=True,
        row_styles=["none", "dim"],
    )
    worker_table.add_column("Worker", justify="center")
    worker_table.add_column("Status", justify="left")
    worker_table.add_column("Details", justify="left")
    
    # Add rows for each task type
    worker_table.add_row("Spider", "Idle", "")
    worker_table.add_row("Profile Collector", "Idle", "")
    worker_table.add_row("Post Collector", "Idle", "")

    layout = Panel(
        worker_table,
        title="Blue Sky Scraper",
        border_style="bold blue",
        padding=(1, 2),
    )
    return layout

app = typer.Typer()

@app.command()
def spider(
    seed_user: str = typer.Option(None, "--seed-user", "-s", help="Seed user handle to start spidering from."),
    limit: int = typer.Option(10, "--limit", "-l", help="Number of users to discover.")
):
    """Run the spider task to discover new users."""
    async def _run():
        async with SessionManager() as sm:
            hive_mind = HiveMind()
            spider_task = SpiderTask(sm, hive_mind)
            
            user_to_spider = seed_user
            if not user_to_spider:
                with open("seed_users.txt", "r") as f:
                    seed_url = f.read().strip()
                    user_to_spider = seed_url.split("/")[-1]

            await spider_task.run(user_to_spider)
    
    asyncio.run(_run())

@app.command()
def collect_profiles(limit: int = typer.Option(10, "--limit", "-l", help="Number of profiles to collect.")):
    """Run the profile collector task."""
    async def _run():
        async with SessionManager() as sm:
            hive_mind = HiveMind()
            profile_collector = ProfileCollectorTask(sm, hive_mind)
            hive_mind.limit = limit
            await profile_collector.run()

    asyncio.run(_run())

@app.command()
def collect_posts(limit: int = typer.Option(5, "--limit", "-l", help="Number of users to collect posts for.")):
    """Run the post collector task."""
    async def _run():
        async with SessionManager() as sm:
            hive_mind = HiveMind()
            post_collector = PostCollectorTask(sm, hive_mind)
            hive_mind.limit = limit
            await post_collector.run()
    
    asyncio.run(_run())

@app.command()
def run_pipeline(
    seed_user: str = typer.Option(None, "--seed-user", "-s", help="Seed user handle to start spidering from."),
    profile_limit: int = typer.Option(10, "--profile-limit", help="Number of profiles to collect."),
    post_limit: int = typer.Option(5, "--post-limit", help="Number of users to collect posts for.")
):
    """Runs the full data collection pipeline."""
    async def _run():
        async with SessionManager() as sm:
            hive_mind = HiveMind()
            
            # --- SPIDER TASK ---
            spider_task = SpiderTask(sm, hive_mind)
            user_to_spider = seed_user
            if not user_to_spider:
                with open("seed_users.txt", "r") as f:
                    seed_url = f.read().strip()
                    user_to_spider = seed_url.split("/")[-1]
            await spider_task.run(user_to_spider)

            # --- PROFILE COLLECTOR TASK ---
            profile_collector = ProfileCollectorTask(sm, hive_mind)
            hive_mind.limit = profile_limit
            await profile_collector.run()

            # --- POST COLLECTOR TASK ---
            post_collector = PostCollectorTask(sm, hive_mind)
            hive_mind.limit = post_limit
            await post_collector.run()

    console = Console()
    console.print("[bold green]Starting Blue Sky Scraper Pipeline...[/bold green]")
    asyncio.run(_run())
    console.print("[bold green]Pipeline finished.[/bold green]")


if __name__ == "__main__":
    app()