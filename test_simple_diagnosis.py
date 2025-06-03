#!/usr/bin/env python3
"""
Simple diagnostic test for match data scraping
"""

import asyncio
import sys
import os
sys.path.append('/app/batch_scraper')

from batch_scraper.fbref_batch_scraper import FBrefBatchScraper
from batch_scraper.config import Config
from batch_scraper.data_processor import DataProcessor
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_single_match():
    """Test comprehensive scraper with a known match URL"""
    
    # Use a recent Premier League match URL
    test_url = "https://fbref.com/en/matches/cc5b4244/Manchester-United-Fulham-August-16-2024-Premier-League"
    
    print(f"🔍 Testing comprehensive scraper with: {test_url}")
    
    config = Config()
    config.RATE_LIMIT_DELAY = 1
    config.HEADLESS = True
    
    scraper = FBrefBatchScraper(config)
    processor = DataProcessor()
    
    try:
        # Setup browser
        print("Setting up browser...")
        if not await scraper.setup_browser():
            print("❌ Failed to setup browser")
            return
        
        print("Extracting match data...")
        # Extract comprehensive data
        comprehensive_data = await scraper.extract_all_match_data(test_url, "2024-25")
        
        if not comprehensive_data:
            print("❌ No data extracted")
            return
        
        print(f"✅ Raw data extracted:")
        metadata = comprehensive_data.get('metadata', {})
        print(f"   - Tables found: {metadata.get('total_tables_found', 0)}")
        print(f"   - Data points: {metadata.get('total_data_points', 0)}")
        print(f"   - Page title: {metadata.get('page_title', 'Unknown')}")
        
        # Check what tables we found
        all_tables = comprehensive_data.get('all_tables', {})
        print(f"\n📊 Analyzing {len(all_tables)} tables:")
        
        team_stats_found = False
        player_stats_found = False
        
        for i, (table_key, table_data) in enumerate(all_tables.items()):
            table_metadata = table_data.get('table_metadata', {})
            data_stat_mapping = table_data.get('data_stat_mapping', {})
            
            table_id = table_metadata.get('id', 'no_id')
            print(f"   Table {i+1}: ID='{table_id}', data-stats: {len(data_stat_mapping)}")
            
            # Check for team stats
            team_indicators = ['poss', 'shots', 'fouls', 'cards_yellow']
            team_stats_count = sum(1 for stat in team_indicators if stat in data_stat_mapping)
            if team_stats_count >= 2:
                team_stats_found = True
                print(f"      ✅ Likely team stats table (found {team_stats_count}/4 indicators)")
                print(f"      Data-stats: {list(data_stat_mapping.keys())[:10]}...")
            
            # Check for player stats
            player_indicators = ['minutes', 'goals', 'assists', 'player_name']
            player_stats_count = sum(1 for stat in player_indicators if stat in data_stat_mapping)
            if player_stats_count >= 2:
                player_stats_found = True
                print(f"      ✅ Likely player stats table (found {player_stats_count}/4 indicators)")
        
        print(f"\n📈 Analysis Results:")
        print(f"   - Team stats table found: {'✅' if team_stats_found else '❌'}")
        print(f"   - Player stats table found: {'✅' if player_stats_found else '❌'}")
        
        # Process the data
        print(f"\n🔄 Processing data...")
        processed_data = processor.process_comprehensive_data(comprehensive_data)
        
        match_info = processed_data.get('match_info', {})
        team_summary = processed_data.get('team_summary', [])
        player_stats = processed_data.get('player_stats', [])
        
        print(f"✅ Processed results:")
        print(f"   - Match info extracted: {'✅' if match_info.get('home_team') else '❌'}")
        print(f"   - Home team: {match_info.get('home_team', 'Unknown')}")
        print(f"   - Away team: {match_info.get('away_team', 'Unknown')}")
        print(f"   - Team summary records: {len(team_summary)}")
        print(f"   - Player stats records: {len(player_stats)}")
        
        if team_summary:
            print(f"   - Sample team stat keys: {list(team_summary[0].keys())[:10]}")
        
        if player_stats:
            print(f"   - Sample player stat keys: {list(player_stats[0].keys())[:10]}")
        
        await scraper.cleanup()
        
        # Summary
        if team_stats_found and player_stats_found and len(team_summary) > 0 and len(player_stats) > 0:
            print(f"\n🎉 SUCCESS: All components working correctly!")
            return True
        else:
            print(f"\n⚠️ ISSUES: Some components not working as expected")
            return False
        
    except Exception as e:
        print(f"❌ Error: {e}")
        await scraper.cleanup()
        return False

if __name__ == "__main__":
    asyncio.run(test_single_match())