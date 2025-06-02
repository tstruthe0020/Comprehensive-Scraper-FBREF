#!/usr/bin/env python3
"""
Single Match Report HTML Structure Analyzer

This script analyzes the HTML structure of a single FBref match report
to validate current CSS selectors and document real data locations.

Test URL: https://fbref.com/en/matches/9c4f2bcd/Brentford-West-Ham-United-September-28-2024-Premier-League
"""

import asyncio
import logging
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import json
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Test match URL
TEST_URL = "https://fbref.com/en/matches/9c4f2bcd/Brentford-West-Ham-United-September-28-2024-Premier-League"

async def setup_playwright_browser():
    """Setup Playwright browser with same config as main scraper"""
    try:
        playwright = await async_playwright().start()
        
        browser = await playwright.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-dev-shm-usage", 
                "--disable-gpu",
                "--disable-software-rasterizer",
                "--disable-extensions",
                "--disable-plugins",
                "--disable-images",
                "--disable-web-security",
                "--single-process"
            ]
        )
        
        page = await browser.new_page(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (X11; Linux aarch64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36"
        )
        
        logger.info("Browser setup successful")
        return playwright, browser, page
    except Exception as e:
        logger.error(f"Browser setup failed: {e}")
        raise

async def navigate_with_retry(page, url, max_retries=3):
    """Navigate with retry logic"""
    for attempt in range(max_retries):
        try:
            logger.info(f"Navigation attempt {attempt + 1} to {url}")
            await page.goto(url, wait_until='networkidle', timeout=30000)
            logger.info("Navigation successful")
            return True
        except Exception as e:
            logger.warning(f"Navigation attempt {attempt + 1} failed: {e}")
            if attempt == max_retries - 1:
                raise e
            await asyncio.sleep(2 ** attempt)  # Exponential backoff
    return False

async def analyze_scorebox_structure(soup):
    """Analyze the scorebox div structure"""
    print("\n" + "="*80)
    print("📊 SCOREBOX ANALYSIS")
    print("="*80)
    
    scorebox = soup.find("div", class_="scorebox")
    if scorebox:
        print("✅ FOUND: div.scorebox exists")
        print(f"   HTML: {str(scorebox)[:500]}...")
        
        # Check for team names
        teams = scorebox.find_all("div", itemprop="name")
        if teams:
            print(f"✅ FOUND: {len(teams)} team names with itemprop='name'")
            for i, team in enumerate(teams):
                print(f"   Team {i+1}: {team.get_text().strip()}")
        else:
            print("❌ NOT FOUND: div[itemprop='name'] for team names")
            
        # Check for scores
        scores = scorebox.find_all("div", class_="score")
        if scores:
            print(f"✅ FOUND: {len(scores)} score divs")
            for i, score in enumerate(scores):
                print(f"   Score {i+1}: {score.get_text().strip()}")
        else:
            print("❌ NOT FOUND: div.score for scores")
            
        # Alternative score selectors
        score_alternatives = [
            ("strong", {}),
            ("span", {"class": "score"}),
            ("div", {"data-stat": "score"})
        ]
        
        for tag, attrs in score_alternatives:
            alt_scores = scorebox.find_all(tag, attrs)
            if alt_scores:
                print(f"🔍 ALTERNATIVE: Found {len(alt_scores)} {tag} elements with {attrs}")
                for i, score in enumerate(alt_scores):
                    print(f"   Alt Score {i+1}: {score.get_text().strip()}")
    else:
        print("❌ CRITICAL: div.scorebox NOT FOUND")
        
        # Try alternative scorebox selectors
        alternatives = [
            ("div", {"id": "scorebox"}),
            ("div", {"class": "score-box"}),
            ("div", {"class": "scores"}),
            ("div", {"id": "scores"})
        ]
        
        for tag, attrs in alternatives:
            alt_scorebox = soup.find(tag, attrs)
            if alt_scorebox:
                print(f"🔍 ALTERNATIVE SCOREBOX: {tag} with {attrs}")
                print(f"   HTML: {str(alt_scorebox)[:300]}...")

async def analyze_table_structure(soup):
    """Analyze all tables and their IDs"""
    print("\n" + "="*80)
    print("📋 TABLE STRUCTURE ANALYSIS")
    print("="*80)
    
    all_tables = soup.find_all('table')
    print(f"Found {len(all_tables)} total tables")
    
    team_stats_tables = []
    player_stats_tables = []
    other_tables = []
    
    for i, table in enumerate(all_tables):
        table_id = table.get('id', f'no-id-{i}')
        table_classes = table.get('class', [])
        
        # Get first few rows for structure analysis
        rows = table.find_all('tr')[:3]
        sample_text = ' '.join([row.get_text(strip=True)[:50] for row in rows])
        
        print(f"\nTable {i+1}:")
        print(f"  ID: {table_id}")
        print(f"  Classes: {table_classes}")
        print(f"  Rows: {len(table.find_all('tr'))}")
        print(f"  Sample: {sample_text}...")
        
        # Categorize tables
        if 'stats' in table_id.lower():
            if any(keyword in table_id.lower() for keyword in ['summary', 'passing', 'defense', 'possession', 'misc']):
                team_stats_tables.append((table_id, table))
            else:
                player_stats_tables.append((table_id, table))
        else:
            other_tables.append((table_id, table))
    
    print(f"\n📊 CATEGORIZED TABLES:")
    print(f"  Team Stats Tables: {len(team_stats_tables)}")
    print(f"  Player Stats Tables: {len(player_stats_tables)}")
    print(f"  Other Tables: {len(other_tables)}")
    
    return {
        'team_stats': team_stats_tables,
        'player_stats': player_stats_tables,
        'other': other_tables
    }

async def test_current_selectors(soup):
    """Test current CSS selectors from the main scraper"""
    print("\n" + "="*80)
    print("🧪 TESTING CURRENT SELECTORS")
    print("="*80)
    
    # Test scorebox selectors
    scorebox_tests = [
        ("div.scorebox", "Main scorebox"),
        ("div[itemprop='name']", "Team names"),
        ("div.score", "Score elements"),
    ]
    
    for selector, description in scorebox_tests:
        elements = soup.select(selector)
        if elements:
            print(f"✅ {description}: {selector} - Found {len(elements)} elements")
        else:
            print(f"❌ {description}: {selector} - NOT FOUND")
    
    # Test team stats table selectors
    team_table_tests = [
        ("table[id*='stats_summary']", "Team summary stats"),
        ("table[id*='stats_passing']", "Team passing stats"),
        ("table[id*='stats_defense']", "Team defense stats"),
        ("table[id*='stats_possession']", "Team possession stats"),
        ("table[id*='stats_misc']", "Team misc stats"),
    ]
    
    for selector, description in team_table_tests:
        elements = soup.select(selector)
        if elements:
            print(f"✅ {description}: {selector} - Found {len(elements)} tables")
        else:
            print(f"❌ {description}: {selector} - NOT FOUND")
    
    # Test data-stat selectors
    data_stat_tests = [
        ("td[data-stat='possession']", "Possession data"),
        ("td[data-stat='shots_total']", "Shots data"),
        ("td[data-stat='shots_on_target']", "Shots on target"),
        ("td[data-stat='xg']", "Expected goals"),
        ("td[data-stat='fouls']", "Fouls data"),
    ]
    
    for selector, description in data_stat_tests:
        elements = soup.select(selector)
        if elements:
            print(f"✅ {description}: {selector} - Found {len(elements)} cells")
            # Show sample values
            for i, elem in enumerate(elements[:3]):
                print(f"   Sample {i+1}: {elem.get_text().strip()}")
        else:
            print(f"❌ {description}: {selector} - NOT FOUND")

async def analyze_match_metadata(soup):
    """Analyze match metadata structure"""
    print("\n" + "="*80)
    print("📋 MATCH METADATA ANALYSIS")
    print("="*80)
    
    # Test date selectors
    date_selectors = [
        ("span.venuetime", "Main date selector"),
        ("span[data-venue-date]", "Date with data attribute"),
        ("div.scorebox_meta", "Scorebox metadata"),
    ]
    
    for selector, description in date_selectors:
        elements = soup.select(selector)
        if elements:
            print(f"✅ {description}: {selector}")
            for elem in elements:
                print(f"   Text: {elem.get_text().strip()}")
                if elem.get('data-venue-date'):
                    print(f"   Date attr: {elem.get('data-venue-date')}")
        else:
            print(f"❌ {description}: {selector} - NOT FOUND")
    
    # Test info box selectors
    info_selectors = [
        ("div#info_box", "Info box by ID"),
        ("div.info_box", "Info box by class"),
        ("div[class*='info']", "Any div with 'info' in class"),
    ]
    
    for selector, description in info_selectors:
        elements = soup.select(selector)
        if elements:
            print(f"✅ {description}: {selector}")
            for elem in elements:
                text = elem.get_text().strip()[:200]
                print(f"   Content: {text}...")
        else:
            print(f"❌ {description}: {selector} - NOT FOUND")

async def generate_structure_report(soup, tables_info):
    """Generate comprehensive structure report"""
    print("\n" + "="*80)
    print("📄 COMPREHENSIVE STRUCTURE REPORT")
    print("="*80)
    
    report = {
        "analysis_date": datetime.now().isoformat(),
        "test_url": TEST_URL,
        "page_title": soup.find('title').get_text() if soup.find('title') else "No title",
        "scorebox_exists": bool(soup.find("div", class_="scorebox")),
        "total_tables": len(soup.find_all('table')),
        "tables": {
            "team_stats_count": len(tables_info['team_stats']),
            "player_stats_count": len(tables_info['player_stats']),
            "other_count": len(tables_info['other']),
            "team_stats_ids": [table_id for table_id, _ in tables_info['team_stats']],
            "player_stats_ids": [table_id for table_id, _ in tables_info['player_stats']],
        },
        "selector_validation": {},
        "recommendations": []
    }
    
    # Test key selectors and add to report
    key_selectors = {
        "scorebox": "div.scorebox",
        "team_names": "div[itemprop='name']",
        "scores": "div.score",
        "match_date": "span.venuetime",
        "info_box": "div#info_box"
    }
    
    for name, selector in key_selectors.items():
        elements = soup.select(selector)
        report["selector_validation"][name] = {
            "selector": selector,
            "found": len(elements),
            "working": len(elements) > 0
        }
    
    # Generate recommendations
    if not report["scorebox_exists"]:
        report["recommendations"].append("CRITICAL: div.scorebox not found - need alternative score extraction")
    
    if report["tables"]["team_stats_count"] == 0:
        report["recommendations"].append("WARNING: No team stats tables found with current ID patterns")
    
    if report["tables"]["player_stats_count"] == 0:
        report["recommendations"].append("WARNING: No player stats tables found")
    
    # Save report to file
    with open('/app/match_structure_analysis.json', 'w') as f:
        json.dump(report, f, indent=2)
    
    print("✅ Report saved to /app/match_structure_analysis.json")
    
    return report

async def main():
    """Main analysis function"""
    print("🎭 FBREF MATCH REPORT HTML STRUCTURE ANALYZER")
    print("="*80)
    print(f"Test URL: {TEST_URL}")
    print(f"Analysis started at: {datetime.now()}")
    
    try:
        # Setup browser
        print("\n🚀 Setting up Playwright browser...")
        playwright, browser, page = await setup_playwright_browser()
        
        # Navigate to test URL
        print(f"📡 Navigating to test URL...")
        await navigate_with_retry(page, TEST_URL)
        
        # Get page content
        print("📄 Extracting page content...")
        content = await page.content()
        soup = BeautifulSoup(content, 'html.parser')
        
        # Perform analysis
        await analyze_scorebox_structure(soup)
        tables_info = await analyze_table_structure(soup)
        await test_current_selectors(soup)
        await analyze_match_metadata(soup)
        report = await generate_structure_report(soup, tables_info)
        
        print("\n" + "="*80)
        print("✅ ANALYSIS COMPLETE")
        print("="*80)
        print(f"Total tables found: {report['total_tables']}")
        print(f"Scorebox exists: {report['scorebox_exists']}")
        print(f"Team stats tables: {report['tables']['team_stats_count']}")
        print(f"Working selectors: {sum(1 for v in report['selector_validation'].values() if v['working'])}/{len(report['selector_validation'])}")
        
        if report['recommendations']:
            print("\n⚠️  CRITICAL RECOMMENDATIONS:")
            for rec in report['recommendations']:
                print(f"   - {rec}")
        
        # Cleanup
        await page.close()
        await browser.close()
        await playwright.stop()
        
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())