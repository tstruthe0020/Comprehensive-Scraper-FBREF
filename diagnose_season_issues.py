#!/usr/bin/env python3
"""
Analysis of what needs to be fixed for full season scraping
"""

import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup

async def diagnose_season_scraping_issues():
    print("🔍 DIAGNOSING FULL SEASON SCRAPING ISSUES")
    print("="*70)
    
    # Issue 1: Fixtures URL and page structure
    print("\n1️⃣  FIXTURES URL & PAGE STRUCTURE ANALYSIS")
    print("-" * 50)
    
    season_urls = [
        ("2024-25 Current", "https://fbref.com/en/comps/9/schedule/Premier-League-Scores-and-Fixtures"),
        ("2023-24 Historical", "https://fbref.com/en/comps/9/2023-2024/schedule/2023-2024-Premier-League-Scores-and-Fixtures"),
        ("Alternative Current", "https://fbref.com/en/comps/9/Premier-League-Stats"),
        ("Fixtures Only", "https://fbref.com/en/comps/9/fixtures/Premier-League-Fixtures")
    ]
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        
        for name, url in season_urls:
            print(f"\n🔗 Testing: {name}")
            print(f"   URL: {url}")
            
            try:
                page = await browser.new_page()
                await page.goto(url, timeout=30000)
                
                title = await page.title()
                print(f"   Title: {title}")
                
                content = await page.content()
                soup = BeautifulSoup(content, 'html.parser')
                
                # Check for match links
                match_links = soup.find_all('a', href=lambda x: x and '/matches/' in x and len(x.split('/')) > 4)
                print(f"   Match links found: {len(match_links)}")
                
                if match_links:
                    print(f"   Sample links:")
                    for i, link in enumerate(match_links[:3]):
                        href = link.get('href')
                        text = link.get_text().strip()[:30]
                        print(f"      {i+1}. {text} -> {href}")
                    
                    # Check if these are real match URLs
                    first_link = match_links[0].get('href')
                    if first_link.startswith('/'):
                        full_url = f"https://fbref.com{first_link}"
                        print(f"   ✅ POTENTIAL WORKING URL: {full_url}")
                    
                # Check for tables with fixtures
                tables = soup.find_all('table')
                print(f"   Tables found: {len(tables)}")
                
                for i, table in enumerate(tables):
                    table_id = table.get('id', f'table-{i}')
                    rows = len(table.find_all('tr'))
                    if rows > 10:  # Potentially a fixtures table
                        print(f"      Large table: {table_id} ({rows} rows)")
                
                await page.close()
                
            except Exception as e:
                print(f"   ❌ Error: {e}")
        
        await browser.close()
    
    print(f"\n2️⃣  CURRENT FIXTURES EXTRACTION LOGIC ISSUES")
    print("-" * 50)
    
    issues = [
        "🔗 URL Pattern: Current season URL might be wrong",
        "📊 Table Selectors: Looking for wrong table IDs/classes", 
        "🎯 Link Extraction: Match URL pattern recognition failing",
        "📅 Date Logic: Season detection logic might be off",
        "🔄 Page Loading: Might need different wait conditions"
    ]
    
    for issue in issues:
        print(f"   ❌ {issue}")
    
    print(f"\n3️⃣  REQUIRED FIXES FOR FULL SEASON SCRAPING")
    print("-" * 50)
    
    fixes_needed = [
        {
            "priority": "🔴 CRITICAL",
            "issue": "Fix Fixtures URL Pattern",
            "description": "Current URLs returning wrong/empty data",
            "solution": "Test different URL patterns, investigate FBref structure changes",
            "effort": "2-3 hours"
        },
        {
            "priority": "🔴 CRITICAL", 
            "issue": "Update Table Selectors",
            "description": "extract_season_fixtures() finding 0 matches",
            "solution": "Analyze real fixtures page HTML, update CSS selectors",
            "effort": "1-2 hours"
        },
        {
            "priority": "🟡 HIGH",
            "issue": "Implement Rate Limiting",
            "description": "No delays between 380+ match requests",
            "solution": "Add configurable delays, respect robots.txt",
            "effort": "1 hour"
        },
        {
            "priority": "🟡 HIGH",
            "issue": "Batch Error Handling", 
            "description": "One failed match breaks entire season",
            "solution": "Continue on individual failures, retry logic",
            "effort": "1-2 hours"
        },
        {
            "priority": "🟡 MEDIUM",
            "issue": "Database Storage Testing",
            "description": "End-to-end storage not verified",
            "solution": "Test full pipeline: scrape → store → verify",
            "effort": "1 hour"
        },
        {
            "priority": "🟢 LOW",
            "issue": "Progress Monitoring",
            "description": "Real-time progress tracking",
            "solution": "Enhanced status updates, ETA calculations",
            "effort": "30 minutes"
        }
    ]
    
    print(f"{'Priority':<12} {'Issue':<25} {'Effort':<10} {'Description'}")
    print("-" * 80)
    
    total_effort = 0
    critical_fixes = 0
    
    for fix in fixes_needed:
        priority = fix['priority']
        issue = fix['issue']
        effort = fix['effort']
        description = fix['description']
        
        print(f"{priority:<12} {issue:<25} {effort:<10} {description}")
        
        if 'CRITICAL' in priority:
            critical_fixes += 1
        
        # Extract effort hours (rough estimate)
        if 'hours' in effort:
            hours = effort.split()[0].split('-')
            if len(hours) == 2:
                total_effort += (int(hours[0]) + int(hours[1])) / 2
            else:
                total_effort += int(hours[0])
    
    print(f"\n📊 EFFORT ESTIMATION")
    print("-" * 30)
    print(f"Critical fixes needed: {critical_fixes}")
    print(f"Total estimated effort: {total_effort:.1f} hours")
    print(f"Minimum viable fixes: 2 critical items (3-5 hours)")
    
    print(f"\n4️⃣  STEP-BY-STEP FIX PLAN")
    print("-" * 50)
    
    plan_steps = [
        "1. 🔍 Investigate FBref fixtures page structure changes",
        "2. 🛠️  Update get_season_fixtures_url() method with correct URLs",
        "3. 🎯 Fix extract_season_fixtures() table selectors",
        "4. 🧪 Test with one season (e.g., 2023-24) to get ~380 fixtures",
        "5. ⚡ Add rate limiting (2-3 seconds between matches)",
        "6. 🛡️  Implement robust error handling for batch processing",
        "7. 💾 Test end-to-end: fixtures → scraping → database storage",
        "8. 📊 Add progress monitoring and ETA calculations"
    ]
    
    for step in plan_steps:
        print(f"   {step}")
    
    print(f"\n🎯 IMMEDIATE ACTION ITEMS")
    print("-" * 50)
    print("To get full season scraping working:")
    print("1. 🔴 FIRST: Fix fixtures URL - test different URL patterns")
    print("2. 🔴 SECOND: Update table selectors based on real HTML")
    print("3. 🟡 THIRD: Add rate limiting for production use")
    print("4. 🧪 TEST: Run with small sample (10 matches) before full season")
    
    return fixes_needed

if __name__ == "__main__":
    asyncio.run(diagnose_season_scraping_issues())