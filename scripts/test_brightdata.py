#!/usr/bin/env python3
"""
Test BrightData Web Unlocker API with ChinaXiv
"""

import os
import sys
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

def main() -> int:
    # Load environment
    load_dotenv()

    api_token = os.getenv("BRIGHTDATA_API_KEY")
    zone_name = os.getenv("BRIGHTDATA_ZONE")

    if not api_token:
        print("Error: BRIGHTDATA_API_KEY not found in .env")
        return 1

    if not zone_name:
        print("Error: BRIGHTDATA_ZONE not found in .env")
        return 1

    # Test URL - ChinaXiv browse page sorted by update time
    test_url = "https://chinaxiv.org/abs/list?order=updateTime&pageType=0"

    print(f"Testing BrightData Web Unlocker...")
    print(f"Target URL: {test_url}")
    print(f"API Key: {api_token[:20]}...")
    print()

    # Method 1: Direct API endpoint
    print("=" * 60)
    print("Method 1: Direct API Endpoint")
    print("=" * 60)

    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }

    payload = {
        "zone": zone_name,
        "url": test_url,
        "format": "raw"  # Get raw HTML
    }

    try:
        response = requests.post(
            "https://api.brightdata.com/request",
            headers=headers,
            json=payload,
            timeout=60
        )

        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")

        if response.status_code == 200:
            html = response.text
            print(f"HTML Length: {len(html)} bytes")
            print()

            # Parse and extract paper IDs
            soup = BeautifulSoup(html, 'html.parser')

            # Find paper links (adjust selectors based on actual structure)
            paper_links = soup.find_all('a', href=lambda x: x and '/abs/' in x)

            print(f"Found {len(paper_links)} paper links")
            print("\nFirst 10 papers:")
            for link in paper_links[:10]:
                href = link.get('href', '')
                title = link.get_text(strip=True)
                print(f"  {href} - {title[:60]}...")

            # Save sample HTML for inspection
            os.makedirs('data', exist_ok=True)
            with open('data/brightdata_sample.html', 'w', encoding='utf-8') as f:
                f.write(html)
            print(f"\nSaved sample HTML to data/brightdata_sample.html")

        else:
            print(f"Error: {response.status_code}")
            print(f"Response: {response.text[:500]}")

    except Exception as e:
        print(f"Exception: {e}")
        import traceback
        traceback.print_exc()

    print()
    print("=" * 60)
    print("Test complete!")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
