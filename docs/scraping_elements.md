# Blue Sky Scraping Data Elements (API Based)

This document outlines the specific data elements to be scraped from Blue Sky's public API. This approach supersedes HTML scraping and relies on intercepting network requests to capture clean JSON data.

---

## 1. User Profile

This data is retrieved from the `app.bsky.actor.getProfile` endpoint.

| Data Element | JSON Key | Example |
| :--- | :--- | :--- |
| **DID** | `did` | `did:plc:udnac33pmf2iwcblpeai5a5p` |
| **Handle** | `handle` | `iwillnotbesilenced.bsky.social` |
| **Display Name** | `displayName` | `Raider` |
| **Description** | `description` | `FASCISM IS NOT TO BE DEBATED...` |
| **Avatar URL** | `avatar` | `https://cdn.bsky.app/...` |
| **Banner URL** | `banner` | `https://cdn.bsky.app/...` |
| **Followers Count** | `followersCount` | `41492` |
| **Following Count** | `followsCount` | `12317` |
| **Posts Count** | `postsCount` | `9030` |
| **Pinned Post URI** | `pinnedPost.uri` | `at://did:plc:udnac33...` |

---

## 2. Following List

This data is retrieved from the `app.bsky.graph.getFollows` endpoint. The response contains a `follows` array, and the following keys should be extracted for each user object in the array.

| Data Element | JSON Key | Example |
| :--- | :--- | :--- |
| **DID** | `did` | `did:plc:2mph3xlusws6dl6fqr2gbyjg` |
| **Handle** | `handle` | `tenderlee.bsky.social` |
| **Display Name** | `displayName` | `Michele` |
| **Description** | `description` | `Here for politics. TN Blue voter...` |
| **Avatar URL** | `avatar` | `https://cdn.bsky.app/...` |

---

## 3. User Feed (Posts)

This data is retrieved from the `app.bsky.feed.getAuthorFeed` endpoint. The response contains a `feed` array, and the following keys should be extracted for each `post` object.

| Data Element | JSON Key | Example |
| :--- | :--- | :--- |
| **Post URI** | `post.uri` | `at://did:plc:udnac33.../3ltad2l3cic2h` |
| **Post CID** | `post.cid` | `bafyreihortbkkuzkxxx2hlc4vg6ikzzlia2lqz5jkr7y5hhpf4gw4m3lhi` |
| **Post Text** | `post.record.text` | `Yesterday in LA. the LAPD chased & brutalized...` |
| **Created At** | `post.record.createdAt` | `2025-07-05T17:51:03.020Z` |
| **Reply Count** | `post.replyCount` | `68` |
| **Repost Count**| `post.repostCount` | `215` |
| **Like Count** | `post.likeCount` | `372` |
| **Quote Count** | `post.quoteCount` | `24` |
| **Embed Type** | `post.embed.$type` | `app.bsky.embed.video#view` |
| **Embed Image/Video**| `post.embed.images` or `post.embed.video` | (Contains URLs and metadata) |