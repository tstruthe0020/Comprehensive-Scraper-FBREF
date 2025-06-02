#!/usr/bin/env python3
"""
Comprehensive data verification script - shows all scraped data for manual verification
"""

import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import sys
import json
from datetime import datetime

sys.path.append('/app/backend')
from server import FBrefScraper

TEST_URL = "https://fbref.com/en/matches/9c4f2bcd/Brentford-West-Ham-United-September-28-2024-Premier-League"

async def comprehensive_data_verification():
    print("📊 COMPREHENSIVE DATA VERIFICATION")
    print("="*80)
    print(f"🔗 Source URL: {TEST_URL}")
    print(f"⏰ Verification Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    
    async with async_playwright() as p:
        try:
            # Setup browser and navigate
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto(TEST_URL, timeout=60000)
            content = await page.content()
            soup = BeautifulSoup(content, 'html.parser')
            
            # Create scraper and extract all data
            scraper = FBrefScraper()
            
            print("\n🏷️  MATCH METADATA")
            print("-" * 50)
            metadata = scraper.extract_match_metadata(soup)
            
            for key, value in metadata.items():
                print(f"📋 {key.replace('_', ' ').title()}: {value}")
            
            # Get page title for reference
            page_title = soup.find('title')
            if page_title:
                print(f"📄 Page Title: {page_title.get_text().strip()}")
            
            print(f"\n⚽ MATCH SUMMARY")
            print("-" * 50)
            if metadata.get('home_team') and metadata.get('away_team'):
                home_score = metadata.get('home_score', 'N/A')
                away_score = metadata.get('away_score', 'N/A')
                print(f"🏠 {metadata['home_team']} {home_score} - {away_score} {metadata['away_team']} 🛣️")
                print(f"📅 Date: {metadata.get('match_date', 'N/A')}")
                print(f"🏟️  Stadium: {metadata.get('stadium', 'N/A')}")
                print(f"👨‍⚖️ Referee: {metadata.get('referee', 'N/A')}")
            
            # Extract team stats for both teams
            if metadata.get('home_team') and metadata.get('away_team'):
                home_team = metadata['home_team']
                away_team = metadata['away_team']
                
                print(f"\n📊 TEAM STATISTICS COMPARISON")
                print("="*80)
                
                # Get stats for both teams
                home_stats = scraper.extract_team_stats(soup, home_team)
                away_stats = scraper.extract_team_stats(soup, away_team)
                
                # Create comprehensive comparison
                all_stat_keys = set(home_stats.keys()) | set(away_stats.keys())
                
                print(f"{'Statistic':<25} {'Home (' + home_team + ')':<20} {'Away (' + away_team + ')':<20}")
                print("-" * 70)
                
                for stat in sorted(all_stat_keys):
                    home_val = home_stats.get(stat, 'N/A')
                    away_val = away_stats.get(stat, 'N/A')
                    stat_name = stat.replace('_', ' ').title()
                    print(f"{stat_name:<25} {str(home_val):<20} {str(away_val):<20}")
                
                print("\n📈 DETAILED BREAKDOWN BY CATEGORY")
                print("="*80)
                
                # Group stats by category for better readability
                stat_categories = {
                    "⚽ Attack": ['shots', 'shots_on_target', 'xg'],
                    "🔄 Passing": ['passes', 'passes_pct', 'passes_progressive'],
                    "🛡️  Defense": ['tackles', 'tackles_won', 'interceptions', 'blocks'],
                    "👟 Possession": ['touches', 'dribbles', 'carries'],
                    "📋 Discipline": ['fouls', 'fouled', 'cards_yellow', 'cards_red']
                }
                
                for category, stats_list in stat_categories.items():
                    print(f"\n{category}")
                    print("-" * 30)
                    for stat in stats_list:
                        if stat in all_stat_keys:
                            home_val = home_stats.get(stat, 'N/A')
                            away_val = away_stats.get(stat, 'N/A')
                            stat_name = stat.replace('_', ' ').title()
                            print(f"  {stat_name:<20} {str(home_val):<10} vs {str(away_val):<10}")
                
                # Create JSON export for detailed analysis
                verification_data = {
                    "url": TEST_URL,
                    "verification_time": datetime.now().isoformat(),
                    "metadata": metadata,
                    "team_stats": {
                        "home_team": {
                            "name": home_team,
                            "stats": home_stats
                        },
                        "away_team": {
                            "name": away_team,
                            "stats": away_stats
                        }
                    },
                    "summary": {
                        "total_metadata_fields": len(metadata),
                        "home_team_stats_count": len(home_stats),
                        "away_team_stats_count": len(away_stats),
                        "unique_stats_extracted": len(all_stat_keys)
                    }
                }
                
                # Save detailed data for manual verification
                with open('/app/verification_data.json', 'w') as f:
                    json.dump(verification_data, f, indent=2)
                
                print(f"\n💾 VERIFICATION DATA SAVED")
                print("-" * 50)
                print("📁 File: /app/verification_data.json")
                print(f"📊 Total metadata fields: {len(metadata)}")
                print(f"📊 Home team stats: {len(home_stats)} fields")
                print(f"📊 Away team stats: {len(away_stats)} fields")
                print(f"📊 Unique statistics: {len(all_stat_keys)} types")
                
                print(f"\n✅ VERIFICATION CHECKLIST")
                print("-" * 50)
                print("To manually verify this data, please check:")
                print("1. 🔗 Visit the source URL above")
                print("2. ⚽ Verify the final score matches")
                print("3. 📅 Check the match date is correct")
                print("4. 👨‍⚖️ Confirm referee name")
                print("5. 📊 Compare key stats like shots, passes, tackles")
                print("6. 🏟️  Verify stadium/venue information")
                print("\nAll extracted data is saved in verification_data.json for detailed analysis.")
                
            await browser.close()
            
        except Exception as e:
            print(f"❌ Verification failed: {e}")
            raise

if __name__ == "__main__":
    asyncio.run(comprehensive_data_verification())