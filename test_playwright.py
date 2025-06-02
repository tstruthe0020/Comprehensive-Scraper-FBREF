#!/usr/bin/env python3
"""
Simple Playwright test to verify browser functionality
"""

import asyncio
from playwright.async_api import async_playwright

async def test_playwright():
    async with async_playwright() as p:
        try:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto("https://httpbin.org/get")
            content = await page.content()
            print(f"Page loaded successfully. Content length: {len(content)}")
            await browser.close()
            return True
        except Exception as e:
            print(f"Error: {e}")
            return False

if __name__ == "__main__":
    result = asyncio.run(test_playwright())
    print(f"Test result: {result}")