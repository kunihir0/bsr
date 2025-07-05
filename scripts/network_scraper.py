import asyncio
import json
from playwright.async_api import async_playwright, Request, Response

async def scrape_and_capture_network(urls: list[str], api_filter: str):
    """
    Scrapes a list of URLs using Playwright, captures network requests to a specific API,
    and logs the captured data to a file.

    Args:
        urls (list[str]): The list of URLs to scrape.
        api_filter (str): The base URL to filter network requests by.
    """
    network_data = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        async def handle_response(response: Response):
            if api_filter in response.url:
                try:
                    response_body = await response.text()
                except Exception:
                    response_body = "N/A (e.g., binary content)"

                network_data.append({
                    "type": "response",
                    "url": response.url,
                    "status": response.status,
                    "status_text": response.status_text,
                    "headers": dict(response.headers),
                    "body": response_body,
                    "request_method": response.request.method,
                    "request_url": response.request.url,
                    "from_service_worker": response.from_service_worker,
                    "mime_type": response.headers.get("content-type", "N/A"),
                })
        
        page.on("response", handle_response)

        for url in urls:
            print(f"Navigating to {url} and capturing network data...")
            try:
                await page.goto(url, wait_until="load")
                print("Page loaded. Waiting for 5 seconds for dynamic content to load...")
                await page.wait_for_timeout(5000)
                print("Continuing... Waiting for network idle...")
                await page.wait_for_load_state("networkidle")
                print("Network idle state reached.")
            except Exception as e:
                print(f"An error occurred while navigating to {url}: {e}")

        await browser.close()

    if network_data:
        with open("network_data.json", "w") as f:
            json.dump(network_data, f, indent=4)
        print(f"\nSuccessfully saved {len(network_data)} network events to network_data.json")
    else:
        print("No network data captured.")

# --- Main execution block ---
if __name__ == "__main__":
    target_urls = [
        "https://bsky.app/profile/iwillnotbesilenced.bsky.social",
        "https://bsky.app/profile/iwillnotbesilenced.bsky.social/follows"
    ]
    api_to_log = "https://public.api.bsky.app"

    asyncio.run(scrape_and_capture_network(target_urls, api_to_log))