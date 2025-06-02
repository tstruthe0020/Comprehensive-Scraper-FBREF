#!/usr/bin/env python3
"""
Get real match URLs from current season and then verify random ones
"""

import asyncio
import random
from playwright.async_api import async_playwright
import sys

sys.path.append('/app/backend')
from server import FBrefScraper

async def get_real_match_urls():
    print("🔍 GETTING REAL MATCH URLs FROM 2024-25 SEASON")
    print("="*60)
    
    scraper = FBrefScraper()
    
    try:
        # Setup browser
        success = await scraper.setup_browser()
        if not success:
            print("❌ Failed to setup browser")
            return []
        
        print("✅ Browser setup successful")
        
        # Get real fixtures from 2024-25 season
        print("📡 Extracting fixtures from FBref...")
        fixtures = await scraper.extract_season_fixtures("2024-25")
        
        print(f"✅ Found {len(fixtures)} real match fixtures")
        
        # Show first few for verification
        print("\n📋 SAMPLE FIXTURES:")
        for i, fixture in enumerate(fixtures[:5]):
            print(f"   {i+1}. {fixture.home_team} vs {fixture.away_team}")
            print(f"      URL: {fixture.match_url}")
        
        # Return list of match URLs
        match_urls = [fixture.match_url for fixture in fixtures]
        
        scraper.cleanup()
        return match_urls
        
    except Exception as e:
        print(f"❌ Error getting fixtures: {e}")
        scraper.cleanup()
        return []

async def verify_real_matches():
    print("🎯 GETTING REAL MATCH URLs AND VERIFYING RANDOM SAMPLE")
    print("="*80)
    
    # First get real match URLs
    match_urls = await get_real_match_urls()
    
    if not match_urls:
        print("❌ No match URLs found - cannot proceed with verification")
        return
    
    # Select 5 random matches to verify
    sample_size = min(5, len(match_urls))
    random_urls = random.sample(match_urls, sample_size)
    
    print(f"\n🎲 TESTING {sample_size} RANDOM MATCHES")
    print("="*60)
    
    scraper = FBrefScraper()
    verification_results = []
    
    # Setup browser for verification
    success = await scraper.setup_browser()
    if not success:
        print("❌ Failed to setup browser for verification")
        return
    
    for i, url in enumerate(random_urls, 1):
        print(f"\n🔍 MATCH {i}/{sample_size}: VERIFICATION")
        print("-" * 50)
        print(f"🔗 URL: {url}")
        
        try:
            # Navigate to match page
            await scraper.navigate_with_retry(url)
            
            # Get page content
            content = await scraper.page.content()
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(content, 'html.parser')
            
            # Extract metadata
            metadata = scraper.extract_match_metadata(soup)
            
            home_team = metadata.get('home_team', 'Unknown')
            away_team = metadata.get('away_team', 'Unknown')
            home_score = metadata.get('home_score', 'N/A')
            away_score = metadata.get('away_score', 'N/A')
            match_date = metadata.get('match_date', 'N/A')
            
            print(f"⚽ Match: {home_team} {home_score} - {away_score} {away_team}")
            print(f"📅 Date: {match_date}")
            
            if home_team == 'Unknown' or away_team == 'Unknown':
                print("❌ Failed to extract team names")
                verification_results.append({
                    "url": url,
                    "success": False,
                    "error": "Could not extract team names"
                })
                continue
            
            # Extract team stats
            home_stats = scraper.extract_team_stats(soup, home_team)
            away_stats = scraper.extract_team_stats(soup, away_team)
            
            print(f"📊 Stats extracted - Home: {len(home_stats)} fields, Away: {len(away_stats)} fields")
            
            # Show key stats
            key_stats = ['shots', 'shots_on_target', 'xg', 'passes', 'tackles']
            print(f"\n📈 KEY STATS:")
            for stat in key_stats:
                home_val = home_stats.get(stat, 'N/A')
                away_val = away_stats.get(stat, 'N/A')
                print(f"   {stat.replace('_', ' ').title()}: {home_val} vs {away_val}")
            
            # Sanity check
            if len(home_stats) >= 5 and len(away_stats) >= 5:
                print("✅ Verification successful")
                verification_results.append({
                    "url": url,
                    "match": f"{home_team} {home_score}-{away_score} {away_team}",
                    "date": match_date,
                    "home_stats": len(home_stats),
                    "away_stats": len(away_stats),
                    "success": True
                })
            else:
                print("⚠️  Low stats count - possible extraction issue")
                verification_results.append({
                    "url": url,
                    "success": False,
                    "error": f"Low stats count: {len(home_stats)}, {len(away_stats)}"
                })
                
        except Exception as e:
            print(f"❌ Error: {e}")
            verification_results.append({
                "url": url,
                "success": False,
                "error": str(e)
            })
    
    # Summary
    successful = [r for r in verification_results if r.get('success', False)]
    failed = [r for r in verification_results if not r.get('success', False)]
    
    print(f"\n📊 VERIFICATION SUMMARY")
    print("="*60)
    print(f"✅ Successful: {len(successful)}/{len(verification_results)}")
    print(f"❌ Failed: {len(failed)}")
    print(f"🎯 Success Rate: {len(successful)/len(verification_results)*100:.1f}%")
    
    if successful:
        print(f"\n🏆 SUCCESSFUL MATCHES:")
        for result in successful:
            print(f"   ✅ {result['match']} ({result['home_stats']}+{result['away_stats']} stats)")
    
    if failed:
        print(f"\n⚠️  FAILED MATCHES:")
        for result in failed:
            print(f"   ❌ {result.get('error', 'Unknown error')}")
    
    scraper.cleanup()
    return len(successful), len(verification_results)

if __name__ == "__main__":
    asyncio.run(verify_real_matches())