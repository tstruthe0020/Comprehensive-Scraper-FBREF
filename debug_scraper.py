#!/usr/bin/env python3
"""
Debug script to test what data is actually being extracted
"""

import asyncio
import json
import sys
import os

# Add batch_scraper to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'batch_scraper'))

from batch_scraper.fbref_batch_scraper import FBrefBatchScraper
from batch_scraper.data_processor import DataProcessor
from batch_scraper.config import Config

async def debug_single_match():
    """Debug a single match to see what data is extracted"""
    
    # Test URL - one of our demo URLs
    test_url = "https://fbref.com/en/matches/cc5b4244/Manchester-United-Fulham-August-16-2024-Premier-League"
    
    print(f"Testing match: {test_url}")
    print("="*50)
    
    # Setup scraper
    config = Config()
    scraper = FBrefBatchScraper(config)
    
    try:
        # Setup browser
        if not await scraper.setup_browser():
            print("❌ Failed to setup browser")
            return
        
        print("✅ Browser setup successful")
        
        # Extract data
        print("🔍 Extracting data...")
        comprehensive_data = await scraper.extract_all_match_data(test_url, "2024-25")
        
        if not comprehensive_data:
            print("❌ No data extracted")
            return
        
        print("✅ Data extraction completed")
        print(f"📊 Metadata: {comprehensive_data.get('metadata', {})}")
        
        # Check what tables were found
        all_tables = comprehensive_data.get('all_tables', {})
        print(f"\n📋 Found {len(all_tables)} tables:")
        
        for table_key, table_data in all_tables.items():
            table_metadata = table_data.get('table_metadata', {})
            table_id = table_metadata.get('id', 'no_id')
            headers = table_data.get('headers', [])
            rows = table_data.get('rows', [])
            
            print(f"  • {table_key}: ID='{table_id}', {len(headers)} headers, {len(rows)} rows")
            
            # Show first few headers
            if headers:
                header_texts = [h.get('text', '') for h in headers[:5]]
                print(f"    Headers: {header_texts}")
            
            # Show sample data from first row
            if rows:
                first_row = rows[0]
                data_stat_values = first_row.get('data_stat_values', {})
                print(f"    Sample data: {dict(list(data_stat_values.items())[:3])}")
        
        # Process the data
        print(f"\n🔄 Processing data...")
        processor = DataProcessor()
        processed_data = processor.process_comprehensive_data(comprehensive_data)
        
        print(f"📈 Processed data summary:")
        print(f"  • Match info: {len(processed_data.get('match_info', {}))}")
        print(f"  • Team summary: {len(processed_data.get('team_summary', []))}")
        print(f"  • Player stats: {len(processed_data.get('player_stats', []))}")
        
        # Show sample processed data
        match_info = processed_data.get('match_info', {})
        if match_info:
            print(f"\n🏆 Match Info Sample:")
            for key, value in list(match_info.items())[:5]:
                print(f"  • {key}: {value}")
        
        team_summary = processed_data.get('team_summary', [])
        if team_summary:
            print(f"\n⚽ Team Summary Sample:")
            for i, team in enumerate(team_summary[:2]):
                print(f"  Team {i+1}: {dict(list(team.items())[:3])}")
        
        player_stats = processed_data.get('player_stats', [])
        if player_stats:
            print(f"\n👤 Player Stats Sample:")
            for i, player in enumerate(player_stats[:3]):
                print(f"  Player {i+1}: {dict(list(player.items())[:3])}")
        else:
            print("❌ No player stats processed")
        
        # Save raw data for inspection
        with open('/app/debug_raw_data.json', 'w') as f:
            json.dump(comprehensive_data, f, indent=2, default=str)
        
        with open('/app/debug_processed_data.json', 'w') as f:
            json.dump(processed_data, f, indent=2, default=str)
        
        print(f"\n💾 Raw data saved to: /app/debug_raw_data.json")
        print(f"💾 Processed data saved to: /app/debug_processed_data.json")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await scraper.cleanup()

if __name__ == "__main__":
    asyncio.run(debug_single_match())