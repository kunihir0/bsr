import asyncio
import json
from playwright.async_api import async_playwright, Request, Response

async def scrape_and_capture_network(url: str):
    """
    Scrapes a given URL using Playwright, captures all network requests and responses,
    and logs the captured data to a file.

    Args:
        url (str): The URL to scrape.
    """
    network_data = []

    async with async_playwright() as p:
        # Launch a Chromium browser in headless mode (set headless=False for visual debugging)
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        # Event listener for network requests
        page.on("request", lambda request: network_data.append({
            "type": "request",
            "url": request.url,
            "method": request.method,
            "headers": dict(request.headers),
            "post_data": request.post_data,
            "resource_type": request.resource_type,
            "frame": request.frame.url
        }))

        # Event listener for network responses
        async def handle_response(response: Response):
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

        print(f"Navigating to {url} and capturing network data...")
        try:
            # Navigate to the URL and wait for the 'load' state (all resources loaded)
            await page.goto(url, wait_until="load")
            # Anti-bot measure: wait for a few seconds for the page to settle
            print("Page loaded. Waiting for 5 seconds for dynamic content to load...")
            await page.wait_for_timeout(5000)
            print("Continuing... Waiting for network idle...")
            # Optionally wait for network idle to capture more requests/responses
            await page.wait_for_load_state("networkidle")
            print("Network idle state reached.")
        except Exception as e:
            print(f"An error occurred while navigating to {url}: {e}")
        finally:
            # Close the browser
            await browser.close()

    # Log the captured network data
    if network_data:
        with open("scripts/data/profile_network_data.json", "w") as f:
            json.dump(network_data, f, indent=4)
        print(f"\nSuccessfully saved {len(network_data)} network events to profile_network_data.json")
    else:
        print("No network data captured.")

# --- Main execution block ---
if __name__ == "__main__":
    # Example URL to scrape
    target_url = "https://bsky.app/profile/iwillnotbesilenced.bsky.social" # You can change this to any URL

    # Run the asynchronous function
    asyncio.run(scrape_and_capture_network(target_url))
