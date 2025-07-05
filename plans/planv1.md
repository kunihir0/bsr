# Blue Sky Scraper Development Plan

This document outlines a strategic plan for developing a powerful and scalable Blue Sky scraper using modern Python technologies. The architecture is designed to be asynchronous, type-safe, and modular, using Playwright as the exclusive tool for all browser interaction and data extraction, with a strong emphasis on observability and user experience.

## 1. Core Technologies

- **Playwright**: The primary and sole tool for all data collection. It will handle logging in, navigating the UI, and extracting data, ideally by intercepting background API requests.
- **Asyncio**: As the foundation for our concurrent operations, enabling us to manage multiple scraper instances efficiently.
- **logging (Standard Library)**: The core engine for all event logging. We will create a custom formatter to provide color-coded, context-aware output without adding external logging dependencies.
- **rich**: A powerful library for creating visually pleasing and fluid terminal interfaces. It will be used to display live progress, status tables, and manage the overall console output, integrating seamlessly with the standard `logging` module.
- **Dataclasses**: To create clean, type-safe, and self-documenting data structures.
- **Qdrant**: To implement the "hive mind," a centralized database to store discovered users and manage the scraping queue.
- **Typer**: For creating a clean command-line interface (CLI) with options for verbosity (e.g., `--debug`).
- **uv**: An extremely fast Python package installer and resolver.

## 2. Architectural Overview

The architecture remains the same, but with a new layer for observability. All components will report their status through the centralized logging system, which is then rendered to the console by the Rich-powered UI.

```
+------------------+      +-----------------+      +----------------+
| Account Manager  |----->| Scraper         |----->| Blue Sky       |
+------------------+      | (Playwright)    |      | (Web Interface)|
      |                   +-----------------+      +----------------+
      v                        |  ^                      ^
+------------------+           v  |                      |
| Proxy Manager    |----->| Hive Mind       |                      |
+------------------+      | (Qdrant)        |                      |
                          +-----------------+                      |
                                 |                                 |
                                 v                                 v
                          +------------------------------------------+
                          |   Logging & Visual Interface (Rich)      |
                          +------------------------------------------+
```

## 3. Data Models (using Dataclasses)

The data models remain unchanged.

```python
from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class Account:
    username: str
    password: str

# ... (rest of the models are the same)
```

## 4. Phase 1: User Discovery (Spidering)

The workflow is the same, but with added logging at each step.

### Workflow & Logging:

1.  Main process starts, loading accounts and proxies. (`INFO: Loaded X accounts and Y proxies.`)
2.  A spider task is created for each account. (`INFO: Starting spider worker for account 'user123'.`)
3.  The spider logs into Blue Sky. (`DEBUG: Navigating to login page...`, `INFO: Login successful for 'user123'.`)
4.  The spider navigates to a user's profile. (`DEBUG: Navigating to profile of 'target_user'.`)
5.  It scrapes followers/following, reporting progress. (`DEBUG: Found 50 new handles.`)
6.  It checks the Hive Mind. (`DEBUG: Checking 50 handles against Qdrant.`)
7.  If a handle is new, it's added to Qdrant. (`INFO: Discovered new user 'new_user_abc'. Added to queue.`)
8.  The process repeats. (`DEBUG: Spider for 'user123' picking next target...`)

## 5. Phase 2: Detailed Data Collection (Playwright with Network Interception)

This phase also gets detailed, real-time feedback.

### Workflow & Logging:

1.  A collector task starts. (`INFO: Starting collector worker for account 'user456'.`)
2.  It queries Qdrant for a pending user. (`DEBUG: Fetching new user from Qdrant queue...`, `INFO: Starting collection for user 'new_user_abc'.`)
3.  It logs in and navigates. (`DEBUG: Collector navigating to profile of 'new_user_abc'.`)
4.  The `route` handler is set up. (`DEBUG: Network interception enabled. Listening for feed/thread requests.`)
5.  As it scrolls and data is captured, it logs progress. (`DEBUG: Captured post batch 1/10.`, `INFO: Collected 50 posts for 'new_user_abc'.`)
6.  After completion, the status is updated in Qdrant and logged. (`INFO: Finished collection for 'new_user_abc'. Updating status to 'completed'.`)

## 6. Project Structure

The project structure is updated to include a dedicated configuration for our logger.

```
bluesky_scraper/
├── src/
│   ├── core/
│   │   ├── account_manager.py
│   │   ├── proxy_manager.py
│   │   ├── hive_mind.py
│   │   ├── scraper_worker.py
│   │   └── logger_config.py  # <-- New: Centralized logging setup
│   ├── models/
│   │   └── models.py
│   ├── phases/
│   │   ├── spider.py
│   │   └── collector.py
│   └── main.py
├── accounts.json
├── proxies.json
└── README.md
```

## 7. Logging and Visual Interface

This new section details the implementation of our observability layer.

-   **Standard Library Logging**: The `src/core/logger_config.py` module will contain a function to set up and configure the root logger. It will define a custom `logging.Formatter` that adds ANSI color codes to log messages based on their level (e.g., `INFO` is green, `WARNING` is yellow, `ERROR` is red, `DEBUG` is blue).
-   **Rich for UI**: The `main.py` file will use the `rich` library to create a dynamic layout.
    -   A `rich.live.Live` context will manage the display, preventing screen flicker.
    -   A `rich.table.Table` will show the real-time status of each worker (spider/collector), including its assigned account, current task (e.g., "Spidering: user_x"), and stats (e.g., users found).
    -   A `rich.progress.Progress` bar can show the overall completion of the queued users.
    -   `rich.logging.RichHandler` will be used to direct all log messages into this live display, ensuring logs appear cleanly without breaking the layout.
-   **Debug Mode**: The CLI (using Typer) will have a `--debug` flag. When enabled, the logger's level will be set to `logging.DEBUG`, making the output extremely verbose for troubleshooting. Otherwise, it will default to `logging.INFO`.

## 8. Next Steps

The plan is updated to prioritize setting up the user-facing components first.

1.  **Setup Environment**: Install Python and `uv`. Initialize with `uv init`. Install packages (`uv pip install playwright qdrant-client typer rich`).
2.  **Setup Logging & UI Shell**:
    -   Implement the colored logger in `src/core/logger_config.py`.
    -   In `main.py`, create the basic `rich` layout (e.g., a table for workers) and integrate the logger using `RichHandler`.
3.  **Initial Code**:
    -   Implement data models, `AccountManager`, `ProxyManager`, and `HiveMind`.
    -   Implement the `ScraperWorker` class that handles Playwright setup and teardown, now with logging hooks.
4.  **Develop Phase 1 (UI-based)**:
    -   Create the spider logic, ensuring it emits logs for all major actions that will appear in the `rich` UI.
5.  **Develop Phase 2 (Network Interception)**:
    -   Create the collector logic, also instrumenting it with detailed logging.

This approach ensures that from the very beginning of development, we'll have a clear and visually appealing way to monitor what the scraper is doing, which is invaluable for a project of this complexity.