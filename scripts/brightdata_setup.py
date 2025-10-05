#!/usr/bin/env python3
"""
BrightData Setup - Find or create Web Unlocker zone
"""

import os
from dotenv import load_dotenv

load_dotenv()

API_TOKEN = os.getenv("BRIGHTDATA_API_KEY")

print("=" * 60)
print("BrightData Web Unlocker Setup")
print("=" * 60)
print()
print("Your API Key is configured: " + API_TOKEN[:20] + "...")
print()
print("NEXT STEP: You need to find your 'zone name'")
print()
print("To find your zone name:")
print("1. Go to https://brightdata.com/cp/zones")
print("2. Look for a 'Web Unlocker' zone")
print("3. Click on it and copy the 'Zone name' (e.g., 'web_unlocker1')")
print()
print("If you don't have a Web Unlocker zone:")
print("1. Click 'Add zone' at https://brightdata.com/cp/zones")
print("2. Select 'Web Unlocker' as the product")
print("3. Name it (e.g., 'chinaxiv_scraper')")
print("4. Click 'Create zone'")
print()
print("Once you have the zone name, add it to your .env file:")
print("BRIGHTDATA_ZONE=your_zone_name_here")
print()
print("=" * 60)
