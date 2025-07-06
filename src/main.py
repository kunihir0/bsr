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

async def run_pipeline():
    """Runs the full data collection pipeline."""
    async with SessionManager() as sm:
        hive_mind = HiveMind() # This will now use the config.toml by default
        
        # --- SPIDER TASK ---
        spider = SpiderTask(sm, hive_mind)
        with open("seed_users.txt", "r") as f:
            seed_url = f.read().strip()
            seed_handle = seed_url.split("/")[-1]

        await spider.run(seed_handle)

        # --- PROFILE COLLECTOR TASK ---
        profile_collector = ProfileCollectorTask(sm, hive_mind)
        await profile_collector.run()

        # --- POST COLLECTOR TASK ---
        post_collector = PostCollectorTask(sm, hive_mind)
        await post_collector.run()

def main(debug: bool = typer.Option(False, "--debug", help="Enable debug logging.")):
    """
    Main entry point for the Blue Sky Scraper CLI.
    """
    if debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Debug mode enabled.")

    console = Console()
    
    # For now, we'll run the pipeline directly.
    # The rich Live display is more for a long-running, multi-worker setup.
    # We will adapt this later to show real-time status from the running tasks.
    console.print("[bold green]Starting Blue Sky Scraper Pipeline...[/bold green]")
    asyncio.run(run_pipeline())
    console.print("[bold green]Pipeline finished.[/bold green]")


if __name__ == "__main__":
    typer.run(main)