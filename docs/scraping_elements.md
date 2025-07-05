# Blue Sky Scraping Data Elements

This document outlines the specific data elements to be scraped from a user's profile and "following" list pages on Blue Sky. The selectors and attributes are based on the provided HTML snippets.

## 1. User Profile Page (`profile.html`)

The following data points should be extracted from a user's main profile page.

| Data Element | Selector / Method | Attribute / Content | Example |
| :--- | :--- | :--- | :--- |
| **Display Name** | `div[data-testid="profileHeaderDisplayName"]` | Text Content | `Raider` |
| **Handle** | `div` containing `‪@...‬` | Text Content | `‪@iwillnotbesilenced.bsky.social` |
| **Profile Description**| `div[data-testid="profileHeaderDescription"]` | Text Content | `FASCISM IS NOT TO BE DEBATED...` |
| **Avatar URL** | `div[data-testid="userAvatarImage"] img` | `src` | `https://.../bafkreibo44...` |
| **Banner URL** | `div[data-testid="userBannerImage"] img` | `src` | `https://.../bafkreic64...` |
| **Followers Count** | `a[data-testid="profileHeaderFollowersButton"] span:first-child` | Text Content | `41.4K` |
| **Following Count** | `a[data-testid="profileHeaderFollowsButton"] span:first-child` | Text Content | `12.3K` |
| **Posts Count** | `div` containing `posts` | Text Content (numeric part) | `9K` |

---

## 2. Following List Page (`following.html`)

The following data points should be extracted for *each user* listed on the "following" page. This is the primary source for discovering new users to add to the scraping queue.

| Data Element | Selector / Method | Attribute / Content | Example |
| :--- | :--- | :--- | :--- |
| **Profile Link (DID)**| `a[href^="/profile/did:plc:"]` | `href` | `/profile/did:plc:2mph3xlusws6dl6fqr2gbyjg` |
| **Display Name** | Parent `div` -> `div` with `font-weight: 600` | Text Content | `Michele` |
| **Handle** | Parent `div` -> `div` containing `‪@...‬` | Text Content | `‪@tenderlee.bsky.social` |
| **Description** | `div[data-word-wrap="1"]` | Text Content | `Here for politics. TN Blue voter...` |
| **Avatar URL** | `div[data-testid="userAvatarImage"] img` | `src` | `https://.../bafkreiarwp...` |

### Note on Data Extraction Strategy:

As outlined in the main development plan, the most efficient way to gather this data is by **intercepting network requests**. While these HTML selectors provide a reliable fallback and are excellent for initial analysis, the primary implementation should focus on capturing the JSON responses from the Blue Sky API calls that populate these pages. This avoids brittle, slow, and resource-intensive HTML parsing.