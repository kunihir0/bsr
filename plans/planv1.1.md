Blue Sky Scraper Development Plan

This document outlines a strategic plan for developing a powerful and scalable Blue Sky scraper using modern Python technologies. The architecture is designed as a high-throughput, asynchronous data pipeline capable of producing clean, structured, training-ready datasets for AI models, operating from a single user session.

1. Core Technologies

Playwright: The primary and sole tool for all data collection. Its use is optimized to rely heavily on network request interception rather than slow HTML parsing.

Asyncio: As the foundation for our concurrent operations.

logging (Standard Library): The core engine for all event logging.

rich: A powerful library for creating visually pleasing and fluid terminal interfaces.

Dataclasses: To create clean, type-safe, and self-documenting data structures.

Qdrant: To implement the "hive mind," a centralized database to manage the multi-stage scraping queue with granular statuses.

Typer: For creating a clean command-line interface (CLI).

uv: An extremely fast Python package installer and resolver.

2. Architectural Overview: A Data Pipeline

The architecture is a multi-stage pipeline designed for high throughput. Different worker tasks operate independently, consuming data from one stage and producing it for the next, all within a single authenticated session.

+----------------+   +----------------+   +-------------------+   +--------------------+
|  Spider Task   |-->|  Profile Task  |-->|  Post Task        |-->|  Data Processor &  |
|  (Finds Users) |   |  (Gets Profile)|   |  (Gets Posts)     |   |  Formatter (ETL)   |
+----------------+   +----------------+   +-------------------+   +--------------------+
        |                    |                    |                       ^
        |                    |                    |                       |
        v                    v                    v                       |
+-------------------------------------------------------------+           |
|                     Hive Mind (Qdrant)                      |           |
|    [status: queued] -> [status: profile] -> [status: posts] |           |
+-------------------------------------------------------------+           |
                               |                                          |
                               v                                          |
+-------------------------------------------------------------------------+
|                              Staging Area (Raw JSONL Files)             |
+-------------------------------------------------------------------------+





Spider Task: An asynchronous task that discovers user handles and adds them to the Hive Mind with status: 'queued'.

Profile Collector Task: An asynchronous task that fetches high-level profile data for queued users and updates their status to profile_collected.

Post Collector Task: The most intensive task. It processes profile_collected users to scrape their entire post history, writing the raw data to a staging area and updating the status to posts_collected.

Data Processor & Formatter: A separate, robust process that reads from the staging area, cleans, transforms, and structures the data into a format suitable for AI training, and then loads it into a final destination.

3. Data Models (using Dataclasses)

We will use dataclasses to define the structure of our data, ensuring type safety and clarity. These models are designed to capture all text and media URLs.

from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class Account:
    username: str
    password: str

@dataclass
class Proxy:
    host: str
    port: int
    username: Optional[str] = None
    password: Optional[str] = None

@dataclass
class BlueSkyUser:
    handle: str
    did: str
    display_name: Optional[str] = None
    description: Optional[str] = None
    followers_count: int = 0
    following_count: int = 0
    posts_count: int = 0
    profile_picture_url: Optional[str] = None
    banner_url: Optional[str] = None
    posts: List['Post'] = field(default_factory=list)

@dataclass
class Post:
    uri: str
    cid: str
    author: BlueSkyUser
    text: str
    created_at: str
    reply_count: int = 0
    repost_count: int = 0
    like_count: int = 0
    embed_images: List[str] = field(default_factory=list)
    replies: List['Post'] = field(default_factory=list)




4. Authentication and Session Workflow

The session workflow is enhanced with mid-scrape validation for a single account.

Check for Session File: The scraper checks if a session file (e.g., sessions/default_session.json) exists.

If the file exists, the worker attempts to load it into a new Playwright browser context. It then navigates to a protected page (like the main feed) to verify the session is active. If successful, it proceeds with the scraping task.

If the file does not exist, or if the session is invalid, the worker proceeds to the next step.

Perform Full Login: The scraper navigates to the Blue Sky login page and enters the username and password for the single configured account.

Save Session: Upon a successful new login, the scraper immediately saves the new context state to the session file using context.storage_state(). This ensures the session can be reused on the next run.

Heartbeat Check: During long-running tasks, the scraper will periodically check if the session is still valid (e.g., by quickly loading the home page). If it fails, it will trigger the re-login process (steps 2 and 3) and then resume its task.

5. Phase 1: User Discovery (Spidering)

This phase is now dramatically faster by eliminating UI scraping for user lists and begins with a user-provided list of seed accounts.

Workflow:

The scraper loads a list of initial "seed" users to start the spidering process. This list can be provided via a file or as command-line arguments.

The Spider Task takes a user from the seed list (or a subsequently discovered user) and navigates to their profile.

It sets up a page.route() to intercept network requests for followers/following (e.g., app.bsky.graph.getFollowers).

It programmatically clicks the "Followers" button.

Instead of scraping the screen, it captures the clean JSON response from the intercepted network request, which contains a full batch of users.

It programmatically scrolls or clicks to trigger the loading of subsequent pages, capturing the JSON from each one.

All discovered handles are checked against Qdrant and added to the queue with status: 'queued'.

6. Phase 2: Multi-Stage Data Collection

This phase is broken into a pipeline for scalability, run as a sequence of asynchronous tasks. The goal is to capture all available data, including URLs for all media.

Stage A: Profile Collection

The Profile Collector task fetches users from Qdrant with status: 'queued'.

It navigates to the user's profile and uses network interception to capture the initial profile data JSON. This JSON will contain handles, display names, descriptions, and URLs for profile pictures,  and header banners.

The collected profile data is written to the Staging Area.

The user's status in Qdrant is updated to profile_collected.

Stage B: Post Collection

The Post Collector task fetches users with status: 'profile_collected'.

It navigates to the user's timeline and, using network interception, captures the JSON for every getAuthorFeed request as it scrolls down the page. This JSON will contain post text and URLs for any embedded images along with media.

The raw post data is streamed to the Staging Area.

The user's status in Qdrant is updated to posts_collected.

7. Data Persistence and AI Preprocessing

To handle billions of records and prepare them for AI training, we use a two-step persistence model. This stage will now include archiving images and retaining all personal information.

Staging Area (Raw Data Lake): This will be a simple directory structure (e.g., data/staging/). Workers write raw, unmodified data as line-delimited JSON (.jsonl) files. This ensures we always have a pristine copy of the original data.

Data Processor & Formatter (ETL Script): A completely separate Python script (process_for_ai.py) will run periodically or continuously. Its only job is to perform the Extract, Transform, Load process:

Extract: Scan the staging directory for new .jsonl files.

Transform: For each record, perform a series of preprocessing steps crucial for AI training:

Text Cleaning: Remove HTML, Markdown, and other artifacts. Normalize whitespace and unicode.

Image Archiving: For every image URL found, download the image file and save it to a structured directory path that clearly links the media to its source. The URL in the final dataset will be replaced with this local file path.

Profile Pictures: data/images/{user_did}/pfp.jpg

Header Banners: data/images/{user_did}/banner.jpg

Post Images: data/images/{user_did}/posts/{post_cid}_{image_index}.jpg

Structuring: Convert raw data into useful training formats (e.g., format a post and its replies as a single conversational document, create instruction-following examples).

Load: Save the cleaned, structured data to a final destination, ready for training. This could be another set of .jsonl files in a data/processed/ directory, or a database optimized for large datasets. This processed data should be versioned (e.g., data/processed/v1.0/).

Note on Personally Identifiable Information (PII): As requested, this plan is designed to collect and retain all data as-is, including user handles, display names, and any other potential PII. No redaction will be performed NO CENSORSHIP.

8. Next Steps

The plan is updated to reflect the new pipeline architecture.

Setup Environment: Install Python and uv.

Setup Logging & UI Shell: Implement the logger and rich UI.

Implement Core Logic & Session Management: Implement data models, a simple credential loader, and the enhanced ScraperWorker with heartbeat checks for a single session.

Develop the Pipeline:

Build the Optimized Spider Task.

Build the Profile Collector Task.

Build the Post Collector Task.

Build the separate Data Processor & Formatter script, including the image downloading logic.

This pipeline approach is standard practice for large-scale data acquisition and is essential for producing high-quality datasets for machine learning.