#!/usr/bin/env python3
"""
Test script to diagnose comprehensive match report scraper issues
"""

import asyncio
import sys
import os
sys.path.append('/app/batch_scraper')
sys.path.append('/app')

from integration_wrapper import check_fbref_availability, enhance_excel_with_fbref_data
from batch_scraper.fbref_batch_scraper import FBrefBatchScraper
from batch_scraper.config import Config
from batch_scraper.data_processor import DataProcessor
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_basic_scraper():
    """Test basic URL scraper functionality"""
    print("🔍 Testing Basic URL Scraper...")
    
    # Import the basic scraper function
    from backend.server import scrape_fbref_with_playwright
    
    test_url = "https://fbref.com/en/comps/9/schedule/Premier-League-Scores-and-Fixtures"
    
    try:
        result = await scrape_fbref_with_playwright(test_url)
        
        print(f"✅ Basic scraper test:")
        print(f"   - Success: {result.success}")
        print(f"   - Message: {result.message}")
        print(f"   - Links found: {len(result.links)}")
        if result.links:
            print(f"   - Sample link: {result.links[0]}")
        
        return result.success and len(result.links) > 0, result.links[:3]  # Return first 3 links for testing
        
    except Exception as e:
        print(f"❌ Basic scraper failed: {e}")
        return False, []

async def test_comprehensive_scraper(match_urls):
    """Test comprehensive match data scraper"""
    print("🔍 Testing Comprehensive Match Data Scraper...")
    
    if not match_urls:
        print("❌ No match URLs to test comprehensive scraper")
        return False
    
    config = Config()
    config.RATE_LIMIT_DELAY = 1  # Faster for testing
    config.HEADLESS = True
    
    scraper = FBrefBatchScraper(config)
    processor = DataProcessor()
    
    try:
        # Setup browser
        if not await scraper.setup_browser():
            print("❌ Failed to setup browser for comprehensive scraper")
            return False
        
        # Test with first match URL
        test_url = match_urls[0]
        print(f"Testing with: {test_url}")
        
        # Extract comprehensive data
        comprehensive_data = await scraper.extract_all_match_data(test_url, "2024-25")
        
        if not comprehensive_data:
            print("❌ No comprehensive data extracted")
            return False
        
        print(f"✅ Comprehensive data extracted:")
        print(f"   - Tables found: {comprehensive_data.get('metadata', {}).get('total_tables_found', 0)}")
        print(f"   - Data points: {comprehensive_data.get('metadata', {}).get('total_data_points', 0)}")
        
        # Process the data
        processed_data = processor.process_comprehensive_data(comprehensive_data)
        
        print(f"✅ Data processed:")
        print(f"   - Match info: {bool(processed_data.get('match_info'))}")
        print(f"   - Team summary: {len(processed_data.get('team_summary', []))}")
        print(f"   - Player stats: {len(processed_data.get('player_stats', []))}")
        
        # Check for specific data-stat values
        print(f"\n🔍 Checking data-stat values in tables...")
        all_tables = comprehensive_data.get('all_tables', {})
        
        found_data_stats = set()
        for table_key, table_data in all_tables.items():
            mapping = table_data.get('data_stat_mapping', {})
            found_data_stats.update(mapping.keys())
        
        # Check for important team stats
        important_stats = ['poss', 'shots', 'shots_on_target', 'fouls', 'cards_yellow', 'cards_red']
        found_important = [stat for stat in important_stats if stat in found_data_stats]
        
        print(f"   - Important data-stats found: {found_important}")
        print(f"   - Total unique data-stats: {len(found_data_stats)}")
        
        if len(found_important) >= 3:
            print("✅ Good coverage of important team statistics")
        else:
            print("⚠️ Limited coverage of important team statistics")
        
        await scraper.cleanup()
        return True
        
    except Exception as e:
        print(f"❌ Comprehensive scraper failed: {e}")
        await scraper.cleanup()
        return False

def test_integration_availability():
    """Test if integration wrapper is working"""
    print("🔍 Testing Integration Wrapper...")
    
    try:
        status = check_fbref_availability()
        print(f"✅ Integration wrapper test:")
        print(f"   - Available: {status.get('available', False)}")
        print(f"   - Status: {status.get('status', 'Unknown')}")
        
        if status.get('error'):
            print(f"   - Error: {status.get('error')}")
        
        return status.get('available', False)
        
    except Exception as e:
        print(f"❌ Integration wrapper failed: {e}")
        return False

async def main():
    """Run all diagnostic tests"""
    print("🚀 COMPREHENSIVE SCRAPER DIAGNOSTIC")
    print("=" * 50)
    
    # Test 1: Check integration availability
    integration_ok = test_integration_availability()
    
    # Test 2: Basic URL scraper
    basic_ok, sample_urls = await test_basic_scraper()
    
    # Test 3: Comprehensive scraper
    comprehensive_ok = False
    if basic_ok and sample_urls:
        comprehensive_ok = await test_comprehensive_scraper(sample_urls)
    
    # Summary
    print("\n" + "=" * 50)
    print("🏁 DIAGNOSTIC SUMMARY")
    print("=" * 50)
    print(f"Integration Wrapper: {'✅ OK' if integration_ok else '❌ FAILED'}")
    print(f"Basic URL Scraper:   {'✅ OK' if basic_ok else '❌ FAILED'}")
    print(f"Comprehensive Data:  {'✅ OK' if comprehensive_ok else '❌ FAILED'}")
    
    if all([integration_ok, basic_ok, comprehensive_ok]):
        print("\n🎉 All components working! Ready for CSV workflow implementation.")
    else:
        print("\n⚠️ Issues detected. Need to fix before implementing CSV workflow.")

if __name__ == "__main__":
    asyncio.run(main())