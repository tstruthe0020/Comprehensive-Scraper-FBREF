#!/usr/bin/env python3
"""
Random match verification script - tests 5-10 different matches
"""

import asyncio
import random
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import sys
import json
from datetime import datetime

sys.path.append('/app/backend')
from server import FBrefScraper

# Sample of different Premier League match URLs for verification
RANDOM_MATCH_URLS = [
    # Different teams and dates for variety
    "https://fbref.com/en/matches/9c4f2bcd/Brentford-West-Ham-United-September-28-2024-Premier-League",
    "https://fbref.com/en/matches/a1b2c3d4/Arsenal-Tottenham-September-15-2024-Premier-League",
    "https://fbref.com/en/matches/e5f6g7h8/Manchester-City-Liverpool-October-5-2024-Premier-League",
    "https://fbref.com/en/matches/i9j0k1l2/Chelsea-Brighton-August-31-2024-Premier-League",
    "https://fbref.com/en/matches/m3n4o5p6/Newcastle-United-Everton-September-21-2024-Premier-League",
]

# Let's also try to get some real current season match URLs
REAL_MATCH_SAMPLES = [
    # These are likely to be real - we'll validate them
    "https://fbref.com/en/matches/9c4f2bcd/Brentford-West-Ham-United-September-28-2024-Premier-League",
    "https://fbref.com/en/matches/018e9b2d/Brighton-Hove-Albion-Tottenham-Hotspur-October-6-2024-Premier-League",
    "https://fbref.com/en/matches/26d8c4a4/Arsenal-Southampton-October-5-2024-Premier-League",
    "https://fbref.com/en/matches/78d2c8a5/Manchester-City-Fulham-October-5-2024-Premier-League",
    "https://fbref.com/en/matches/5ce8f74d/Chelsea-Nottingham-Forest-October-6-2024-Premier-League",
]

async def verify_random_matches():
    print("🎲 RANDOM MATCH VERIFICATION TEST")
    print("="*80)
    print(f"🕐 Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Select random matches to test
    test_urls = random.sample(REAL_MATCH_SAMPLES, min(5, len(REAL_MATCH_SAMPLES)))
    
    verification_results = []
    scraper = FBrefScraper()
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        
        for i, url in enumerate(test_urls, 1):
            print(f"\n🔍 MATCH {i}/5: VERIFICATION")
            print("-" * 60)
            print(f"🔗 URL: {url}")
            
            try:
                page = await browser.new_page()
                
                # Navigate with timeout
                print("📡 Loading page...")
                await page.goto(url, timeout=30000, wait_until='networkidle')
                
                # Check if page loaded successfully
                title = await page.title()
                if "404" in title or "Not Found" in title:
                    print(f"❌ Invalid URL - skipping")
                    await page.close()
                    continue
                
                print(f"📄 Title: {title}")
                
                # Get content and parse
                content = await page.content()
                soup = BeautifulSoup(content, 'html.parser')
                
                # Extract data using our scraper
                metadata = scraper.extract_match_metadata(soup)
                
                if not metadata.get('home_team') or not metadata.get('away_team'):
                    print("❌ Could not extract team names - invalid match page")
                    await page.close()
                    continue
                
                home_team = metadata['home_team']
                away_team = metadata['away_team']
                home_score = metadata.get('home_score', 'N/A')
                away_score = metadata.get('away_score', 'N/A')
                
                print(f"⚽ Match: {home_team} {home_score} - {away_score} {away_team}")
                print(f"📅 Date: {metadata.get('match_date', 'N/A')}")
                
                # Extract team stats
                home_stats = scraper.extract_team_stats(soup, home_team)
                away_stats = scraper.extract_team_stats(soup, away_team)
                
                print(f"📊 Home stats extracted: {len(home_stats)} fields")
                print(f"📊 Away stats extracted: {len(away_stats)} fields")
                
                # Show key stats for verification
                key_stats = ['shots', 'shots_on_target', 'xg', 'passes', 'tackles']
                print(f"\n🔍 KEY STATS VERIFICATION:")
                print(f"{'Stat':<15} {'Home':<10} {'Away':<10}")
                print("-" * 35)
                
                for stat in key_stats:
                    home_val = home_stats.get(stat, 'N/A')
                    away_val = away_stats.get(stat, 'N/A')
                    print(f"{stat.replace('_', ' ').title():<15} {str(home_val):<10} {str(away_val):<10}")
                
                # Sanity checks
                sanity_checks = []
                
                # Check if shots seem reasonable (0-50 range)
                home_shots = home_stats.get('shots', 0)
                away_shots = away_stats.get('shots', 0)
                if 0 <= home_shots <= 50 and 0 <= away_shots <= 50:
                    sanity_checks.append("✅ Shots in reasonable range")
                else:
                    sanity_checks.append(f"⚠️  Shots seem unusual: {home_shots}, {away_shots}")
                
                # Check if passes seem reasonable (100-1000 range)
                home_passes = home_stats.get('passes', 0)
                away_passes = away_stats.get('passes', 0)
                if 100 <= home_passes <= 1000 and 100 <= away_passes <= 1000:
                    sanity_checks.append("✅ Passes in reasonable range")
                else:
                    sanity_checks.append(f"⚠️  Passes seem unusual: {home_passes}, {away_passes}")
                
                # Check if xG is reasonable (0-5 range)
                home_xg = home_stats.get('xg', 0)
                away_xg = away_stats.get('xg', 0)
                if 0 <= home_xg <= 5 and 0 <= away_xg <= 5:
                    sanity_checks.append("✅ xG in reasonable range")
                else:
                    sanity_checks.append(f"⚠️  xG seems unusual: {home_xg}, {away_xg}")
                
                print(f"\n🧪 SANITY CHECKS:")
                for check in sanity_checks:
                    print(f"   {check}")
                
                # Store result
                verification_results.append({
                    "url": url,
                    "title": title,
                    "match": f"{home_team} {home_score}-{away_score} {away_team}",
                    "date": metadata.get('match_date'),
                    "home_stats_count": len(home_stats),
                    "away_stats_count": len(away_stats),
                    "key_stats": {
                        "home": {stat: home_stats.get(stat) for stat in key_stats},
                        "away": {stat: away_stats.get(stat) for stat in key_stats}
                    },
                    "sanity_checks": sanity_checks,
                    "success": len(home_stats) > 5 and len(away_stats) > 5
                })
                
                print(f"✅ Match {i} verification complete")
                await page.close()
                
            except Exception as e:
                print(f"❌ Error verifying match {i}: {e}")
                verification_results.append({
                    "url": url,
                    "error": str(e),
                    "success": False
                })
        
        await browser.close()
    
    # Summary
    print(f"\n📊 VERIFICATION SUMMARY")
    print("="*60)
    
    successful = [r for r in verification_results if r.get('success', False)]
    failed = [r for r in verification_results if not r.get('success', False)]
    
    print(f"✅ Successful verifications: {len(successful)}/{len(verification_results)}")
    print(f"❌ Failed verifications: {len(failed)}")
    
    if successful:
        print(f"\n🎯 SUCCESSFUL MATCHES:")
        for result in successful:
            print(f"   ✅ {result['match']} - {result['home_stats_count']}+{result['away_stats_count']} stats")
    
    if failed:
        print(f"\n⚠️  FAILED MATCHES:")
        for result in failed:
            error = result.get('error', 'Unknown error')
            print(f"   ❌ {result['url'][:50]}... - {error}")
    
    # Save detailed results
    with open('/app/random_match_verification.json', 'w') as f:
        json.dump({
            "verification_time": datetime.now().isoformat(),
            "total_tested": len(verification_results),
            "successful": len(successful),
            "failed": len(failed),
            "success_rate": len(successful) / len(verification_results) * 100 if verification_results else 0,
            "results": verification_results
        }, f, indent=2)
    
    print(f"\n💾 Detailed results saved to: /app/random_match_verification.json")
    print(f"🎉 Overall success rate: {len(successful)/len(verification_results)*100:.1f}%")

if __name__ == "__main__":
    asyncio.run(verify_random_matches())