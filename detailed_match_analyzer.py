#!/usr/bin/env python3
"""
Detailed FBref match structure analyzer
"""

import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import json

TEST_URL = "https://fbref.com/en/matches/9c4f2bcd/Brentford-West-Ham-United-September-28-2024-Premier-League"

async def detailed_analysis():
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
            
            # Detailed scorebox analysis
            print("\n" + "="*80)
            print("DETAILED SCOREBOX ANALYSIS")
            print("="*80)
            
            scorebox = soup.find("div", class_="scorebox")
            if scorebox:
                print("📦 Scorebox HTML structure:")
                print(scorebox.prettify()[:1000] + "..." if len(str(scorebox)) > 1000 else scorebox.prettify())
                
                # Look for alternative team name selectors
                team_selectors = [
                    ("div[itemprop='name']", "itemprop name"),
                    ("h1", "h1 tags"),
                    ("strong", "strong tags"),
                    ("a[href*='/squads/']", "squad links"),
                    (".team", "team class"),
                ]
                
                print("\n🔍 Testing team name selectors:")
                for selector, desc in team_selectors:
                    elements = scorebox.select(selector)
                    if elements:
                        print(f"✅ {desc}: {selector}")
                        for i, elem in enumerate(elements):
                            print(f"   Team {i+1}: '{elem.get_text().strip()}'")
                    else:
                        print(f"❌ {desc}: {selector}")
            
            # Detailed table analysis
            print("\n" + "="*80)
            print("DETAILED TABLE ANALYSIS")
            print("="*80)
            
            stats_tables = soup.select("table[id*='stats']")
            print(f"Found {len(stats_tables)} stats tables")
            
            for i, table in enumerate(stats_tables):
                table_id = table.get('id', f'no-id-{i}')
                print(f"\n📊 Table {i+1}: {table_id}")
                
                # Check for data-stat attributes
                data_stat_cells = table.select("td[data-stat]")
                if data_stat_cells:
                    stats = set([cell.get('data-stat') for cell in data_stat_cells[:10]])
                    print(f"   Data stats: {list(stats)}")
                
                # Show first row content
                first_row = table.find('tr')
                if first_row:
                    cells = first_row.find_all(['td', 'th'])
                    if cells:
                        row_text = [cell.get_text().strip()[:15] for cell in cells[:5]]
                        print(f"   First row: {row_text}")
            
            # Test specific data extraction
            print("\n" + "="*80)
            print("DATA EXTRACTION TESTS")
            print("="*80)
            
            # Test possession extraction
            possession_selectors = [
                "td[data-stat='possession']",
                "td:contains('Possession')",
                "*:contains('Possession')",
            ]
            
            for selector in possession_selectors:
                try:
                    if 'contains' in selector:
                        # Use BeautifulSoup for text search
                        elements = soup.find_all(text=lambda text: text and 'Possession' in text)
                        if elements:
                            print(f"✅ Text search 'Possession': Found {len(elements)} elements")
                            for elem in elements[:3]:
                                print(f"   Text: '{elem.strip()}'")
                    else:
                        elements = soup.select(selector)
                        if elements:
                            print(f"✅ {selector}: Found {len(elements)} elements")
                            for elem in elements[:3]:
                                print(f"   Value: '{elem.get_text().strip()}'")
                        else:
                            print(f"❌ {selector}: Not found")
                except Exception as e:
                    print(f"❌ {selector}: Error - {e}")
            
            # Look for team-specific tables
            print("\n" + "="*80)
            print("TEAM-SPECIFIC TABLE SEARCH")
            print("="*80)
            
            team_keywords = ['Brentford', 'West Ham', 'home', 'away']
            for keyword in team_keywords:
                tables_with_keyword = []
                for table in stats_tables:
                    if keyword.lower() in table.get_text().lower():
                        tables_with_keyword.append(table.get('id', 'no-id'))
                
                if tables_with_keyword:
                    print(f"✅ Tables containing '{keyword}': {tables_with_keyword}")
                else:
                    print(f"❌ No tables containing '{keyword}'")
            
            # Save detailed report
            report = {
                "url": TEST_URL,
                "scorebox_exists": bool(scorebox),
                "total_tables": len(soup.find_all('table')),
                "stats_tables": len(stats_tables),
                "stats_table_ids": [table.get('id') for table in stats_tables],
                "working_selectors": {
                    "scorebox": bool(soup.select("div.scorebox")),
                    "scores": bool(soup.select("div.score")),
                    "stats_tables": bool(soup.select("table[id*='stats']")),
                    "team_names_itemprop": bool(soup.select("div[itemprop='name']")),
                    "possession_data": bool(soup.select("td[data-stat='possession']")),
                }
            }
            
            with open('/app/detailed_structure_report.json', 'w') as f:
                json.dump(report, f, indent=2)
            
            print(f"\n✅ Report saved to detailed_structure_report.json")
            print(f"📊 Summary: {report['stats_tables']} stats tables found")
            print(f"🎯 Key selectors working: {sum(report['working_selectors'].values())}/{len(report['working_selectors'])}")
            
            await browser.close()
            
        except Exception as e:
            print(f"❌ Error: {e}")
            raise

if __name__ == "__main__":
    asyncio.run(detailed_analysis())