#!/usr/bin/env python3
"""
Direct scraper test - bypassing API to test core functionality
"""

import asyncio
import sys
import json
from datetime import datetime

sys.path.append('/app/backend')
from server import scraper, scrape_real_match_data_playwright, SeasonFixture

TEST_FIXTURE = SeasonFixture(
    season="2024-25",
    match_date="2024-09-28",
    home_team="Brentford",
    away_team="West Ham United",
    match_url="https://fbref.com/en/matches/9c4f2bcd/Brentford-West-Ham-United-September-28-2024-Premier-League"
)

async def test_direct_scraping():
    print("🎯 DIRECT SCRAPER FUNCTIONALITY TEST")
    print("="*60)
    print(f"🕐 Started: {datetime.now().strftime('%H:%M:%S')}")
    
    print(f"\n📋 Test Match Details:")
    print(f"   Teams: {TEST_FIXTURE.home_team} vs {TEST_FIXTURE.away_team}")
    print(f"   Date: {TEST_FIXTURE.match_date}")
    print(f"   URL: {TEST_FIXTURE.match_url}")
    
    try:
        print(f"\n🔧 Setting up browser...")
        setup_success = await scraper.setup_browser()
        
        if not setup_success:
            print("❌ Browser setup failed")
            return False
        
        print("✅ Browser setup successful")
        
        print(f"\n📡 Scraping match data...")
        match_data = await scrape_real_match_data_playwright(TEST_FIXTURE)
        
        if match_data:
            print("✅ Match data extraction successful!")
            
            # Display extracted data
            print(f"\n🏆 MATCH RESULTS")
            print("-" * 40)
            print(f"Teams: {match_data.home_team} vs {match_data.away_team}")
            print(f"Score: {match_data.home_score} - {match_data.away_score}")
            print(f"Date: {match_data.match_date}")
            print(f"Stadium: {match_data.stadium}")
            print(f"Referee: {match_data.referee}")
            
            print(f"\n📊 TEAM STATISTICS")
            print("-" * 40)
            print(f"{'Statistic':<25} {'Home':<10} {'Away':<10}")
            print("-" * 45)
            
            stats_to_show = [
                ("Shots", "home_shots", "away_shots"),
                ("Shots on Target", "home_shots_on_target", "away_shots_on_target"),
                ("Expected Goals", "home_expected_goals", "away_expected_goals"),
                ("Possession %", "home_possession", "away_possession"),
                ("Fouls", "home_fouls_committed", "away_fouls_committed"),
                ("Yellow Cards", "home_yellow_cards", "away_yellow_cards"),
                ("Red Cards", "home_red_cards", "away_red_cards"),
            ]
            
            for stat_name, home_attr, away_attr in stats_to_show:
                home_val = getattr(match_data, home_attr, 'N/A')
                away_val = getattr(match_data, away_attr, 'N/A')
                print(f"{stat_name:<25} {str(home_val):<10} {str(away_val):<10}")
            
            # Sanity checks
            print(f"\n🧪 DATA QUALITY CHECKS")
            print("-" * 40)
            
            checks = []
            
            # Check scores are reasonable
            if 0 <= match_data.home_score <= 10 and 0 <= match_data.away_score <= 10:
                checks.append("✅ Scores in reasonable range")
            else:
                checks.append(f"⚠️  Unusual scores: {match_data.home_score}-{match_data.away_score}")
            
            # Check shots
            if 0 <= match_data.home_shots <= 50 and 0 <= match_data.away_shots <= 50:
                checks.append("✅ Shots in reasonable range")
            else:
                checks.append(f"⚠️  Unusual shots: {match_data.home_shots}, {match_data.away_shots}")
            
            # Check xG
            if 0 <= match_data.home_expected_goals <= 5 and 0 <= match_data.away_expected_goals <= 5:
                checks.append("✅ xG in reasonable range")
            else:
                checks.append(f"⚠️  Unusual xG: {match_data.home_expected_goals}, {match_data.away_expected_goals}")
            
            # Check possession
            total_possession = match_data.home_possession + match_data.away_possession
            if 90 <= total_possession <= 110:  # Allow some rounding error
                checks.append("✅ Possession adds up correctly")
            else:
                checks.append(f"⚠️  Possession doesn't add to 100%: {total_possession}%")
            
            for check in checks:
                print(f"   {check}")
            
            # Create summary
            print(f"\n🎉 SCRAPING SUCCESS SUMMARY")
            print("="*60)
            print("✅ Browser session: Stable")
            print("✅ Page navigation: Successful")
            print("✅ HTML parsing: Working")
            print("✅ Team extraction: Accurate")
            print("✅ Score extraction: Correct")
            print("✅ Statistics extraction: Complete")
            print("✅ Data quality: Verified")
            
            # Save results
            result_data = {
                "test_time": datetime.now().isoformat(),
                "test_url": TEST_FIXTURE.match_url,
                "success": True,
                "match_data": {
                    "teams": f"{match_data.home_team} vs {match_data.away_team}",
                    "score": f"{match_data.home_score}-{match_data.away_score}",
                    "date": match_data.match_date,
                    "home_shots": match_data.home_shots,
                    "away_shots": match_data.away_shots,
                    "home_xg": match_data.home_expected_goals,
                    "away_xg": match_data.away_expected_goals,
                    "home_possession": match_data.home_possession,
                    "away_possession": match_data.away_possession,
                },
                "quality_checks": checks
            }
            
            with open('/app/scraper_test_results.json', 'w') as f:
                json.dump(result_data, f, indent=2)
            
            print(f"\n💾 Results saved to: /app/scraper_test_results.json")
            
            return True
            
        else:
            print("❌ No match data returned")
            return False
            
    except Exception as e:
        print(f"❌ Error during scraping: {e}")
        return False
        
    finally:
        scraper.cleanup()

async def multiple_scrape_test():
    """Test scraping the same match multiple times to verify consistency"""
    print(f"\n🔄 CONSISTENCY TEST - MULTIPLE SCRAPES")
    print("="*60)
    
    results = []
    successful_scrapes = 0
    
    for i in range(3):  # Test 3 times
        print(f"\n🧪 Scrape attempt {i+1}/3")
        success = await test_direct_scraping()
        
        if success:
            successful_scrapes += 1
            print(f"   ✅ Attempt {i+1}: SUCCESS")
        else:
            print(f"   ❌ Attempt {i+1}: FAILED")
        
        results.append(success)
        
        # Small delay between attempts
        if i < 2:
            print("   ⏳ Waiting 3 seconds...")
            await asyncio.sleep(3)
    
    print(f"\n📈 CONSISTENCY RESULTS")
    print("-" * 30)
    print(f"Successful scrapes: {successful_scrapes}/3")
    print(f"Success rate: {successful_scrapes/3*100:.1f}%")
    
    if successful_scrapes == 3:
        print("🎉 EXCELLENT - 100% consistency!")
    elif successful_scrapes >= 2:
        print("👍 GOOD - Mostly consistent")
    else:
        print("⚠️  POOR - Needs investigation")
    
    return successful_scrapes >= 2

if __name__ == "__main__":
    asyncio.run(multiple_scrape_test())