#!/usr/bin/env python3
"""
Simplified FBref match structure analyzer
"""

import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup

TEST_URL = "https://fbref.com/en/matches/9c4f2bcd/Brentford-West-Ham-United-September-28-2024-Premier-League"

async def analyze_match_structure():
    async with async_playwright() as p:
        try:
            print("🚀 Launching browser...")
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            print(f"📡 Navigating to: {TEST_URL}")
            await page.goto(TEST_URL, timeout=60000)
            
            print("📄 Getting page content...")
            content = await page.content()
            soup = BeautifulSoup(content, 'html.parser')
            
            print("\n" + "="*60)
            print("SCOREBOX ANALYSIS")
            print("="*60)
            
            # Check scorebox
            scorebox = soup.find("div", class_="scorebox")
            if scorebox:
                print("✅ FOUND: div.scorebox")
                
                # Check team names
                teams = scorebox.find_all("div", itemprop="name")
                if teams:
                    print(f"✅ FOUND: {len(teams)} team names")
                    for i, team in enumerate(teams):
                        print(f"   Team {i+1}: {team.get_text().strip()}")
                else:
                    print("❌ Team names not found")
                
                # Check scores
                scores = scorebox.find_all("div", class_="score")
                if scores:
                    print(f"✅ FOUND: {len(scores)} scores")
                    for i, score in enumerate(scores):
                        print(f"   Score {i+1}: {score.get_text().strip()}")
                else:
                    print("❌ Scores not found")
            else:
                print("❌ CRITICAL: div.scorebox NOT FOUND")
            
            print("\n" + "="*60)
            print("TABLE ANALYSIS")
            print("="*60)
            
            # Check tables
            tables = soup.find_all('table')
            print(f"Found {len(tables)} total tables")
            
            for i, table in enumerate(tables[:5]):  # Show first 5 tables
                table_id = table.get('id', f'no-id-{i}')
                rows = len(table.find_all('tr'))
                print(f"Table {i+1}: ID='{table_id}', Rows={rows}")
            
            print("\n" + "="*60)
            print("SELECTOR TESTS")
            print("="*60)
            
            # Test key selectors
            selectors = [
                ("div.scorebox", "Scorebox"),
                ("div[itemprop='name']", "Team names"),
                ("div.score", "Scores"),
                ("table[id*='stats']", "Stats tables"),
                ("td[data-stat='possession']", "Possession data"),
            ]
            
            for selector, description in selectors:
                elements = soup.select(selector)
                status = "✅" if elements else "❌"
                print(f"{status} {description}: {selector} ({len(elements)} found)")
            
            await browser.close()
            
        except Exception as e:
            print(f"❌ Error: {e}")
            raise

if __name__ == "__main__":
    asyncio.run(analyze_match_structure())