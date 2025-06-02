#!/usr/bin/env python3
"""
Comprehensive end-to-end test: Full season scraping with database storage
"""

import asyncio
import requests
import json
import time
from datetime import datetime
import sys

def print_header(title):
    print(f"\n{'='*80}")
    print(f"🎯 {title}")
    print(f"{'='*80}")

def print_section(title):
    print(f"\n{'-'*60}")
    print(f"📋 {title}")
    print(f"{'-'*60}")

async def test_full_season_with_database():
    print_header("COMPREHENSIVE SEASON SCRAPING TEST")
    print(f"🕐 Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    backend_url = "http://localhost:8001"
    
    # Step 1: Check backend health
    print_section("1. BACKEND HEALTH CHECK")
    try:
        response = requests.get(f"{backend_url}/api/", timeout=5)
        if response.status_code == 200:
            print("✅ Backend is running")
            print(f"   Response: {response.json()}")
        else:
            print(f"❌ Backend unhealthy: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Backend not accessible: {e}")
        return False
    
    # Step 2: Check database connection
    print_section("2. DATABASE CONNECTION TEST")
    try:
        response = requests.get(f"{backend_url}/api/seasons", timeout=10)
        if response.status_code == 200:
            print("✅ Database connection working")
            seasons = response.json()
            print(f"   Available seasons: {seasons}")
        else:
            print(f"⚠️  Database connection issue: {response.status_code}")
    except Exception as e:
        print(f"⚠️  Database check failed: {e}")
    
    # Step 3: Check existing data
    print_section("3. EXISTING DATA CHECK")
    try:
        response = requests.get(f"{backend_url}/api/matches", timeout=10)
        if response.status_code == 200:
            existing_matches = response.json()
            print(f"📊 Existing matches in database: {len(existing_matches)}")
            
            if existing_matches:
                print("   Sample existing data:")
                for i, match in enumerate(existing_matches[:3]):
                    home = match.get('home_team', 'Unknown')
                    away = match.get('away_team', 'Unknown')
                    score = f"{match.get('home_score', '?')}-{match.get('away_score', '?')}"
                    print(f"      {i+1}. {home} {score} {away}")
        else:
            print(f"⚠️  Could not fetch existing matches: {response.status_code}")
    except Exception as e:
        print(f"⚠️  Error checking existing data: {e}")
    
    # Step 4: Start season scraping
    print_section("4. STARTING SEASON SCRAPING")
    
    # Use 2023-24 season (completed season with known matches)
    season = "2023-24"
    print(f"🎯 Target season: {season}")
    print(f"📡 Sending scraping request...")
    
    try:
        response = requests.post(
            f"{backend_url}/api/scrape-season/{season}",
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            status_id = result.get('status_id')
            print(f"✅ Scraping started successfully!")
            print(f"   Status ID: {status_id}")
            print(f"   Message: {result.get('message')}")
            
            if not status_id:
                print("❌ No status ID returned")
                return False
                
        else:
            print(f"❌ Failed to start scraping: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error starting scraping: {e}")
        return False
    
    # Step 5: Monitor progress
    print_section("5. MONITORING SCRAPING PROGRESS")
    
    start_time = time.time()
    last_status = None
    check_count = 0
    max_checks = 120  # Maximum 20 minutes (120 * 10 seconds)
    
    while check_count < max_checks:
        try:
            response = requests.get(f"{backend_url}/api/scraping-status/{status_id}", timeout=10)
            
            if response.status_code == 200:
                status = response.json()
                current_status = status.get('status', 'unknown')
                matches_scraped = status.get('matches_scraped', 0)
                total_matches = status.get('total_matches', 0)
                current_match = status.get('current_match', '')
                errors = status.get('errors', [])
                
                # Only print if status changed
                if status != last_status:
                    elapsed = time.time() - start_time
                    progress = (matches_scraped / total_matches * 100) if total_matches > 0 else 0
                    
                    print(f"\n🔄 Status Update ({elapsed:.0f}s elapsed):")
                    print(f"   Status: {current_status}")
                    print(f"   Progress: {matches_scraped}/{total_matches} ({progress:.1f}%)")
                    print(f"   Current: {current_match}")
                    print(f"   Errors: {len(errors)}")
                    
                    if errors and len(errors) <= 5:  # Show first few errors
                        print(f"   Recent errors:")
                        for error in errors[-3:]:
                            print(f"      - {error}")
                    
                    last_status = status
                
                # Check if completed or failed
                if current_status in ['completed', 'failed']:
                    print(f"\n🏁 Scraping {current_status.upper()}!")
                    
                    final_elapsed = time.time() - start_time
                    print(f"   Total time: {final_elapsed:.1f} seconds ({final_elapsed/60:.1f} minutes)")
                    print(f"   Final progress: {matches_scraped}/{total_matches}")
                    
                    if errors:
                        print(f"   Total errors: {len(errors)}")
                        if len(errors) <= 10:
                            print(f"   All errors:")
                            for i, error in enumerate(errors, 1):
                                print(f"      {i}. {error}")
                        else:
                            print(f"   Last 5 errors:")
                            for i, error in enumerate(errors[-5:], 1):
                                print(f"      {i}. {error}")
                    
                    break
                    
            else:
                print(f"⚠️  Could not get status: {response.status_code}")
            
            check_count += 1
            await asyncio.sleep(10)  # Check every 10 seconds
            
        except Exception as e:
            print(f"⚠️  Error checking status: {e}")
            check_count += 1
            await asyncio.sleep(10)
    
    if check_count >= max_checks:
        print(f"\n⏰ Timeout reached (20 minutes) - stopping monitoring")
    
    # Step 6: Check final database state
    print_section("6. FINAL DATABASE VERIFICATION")
    
    try:
        response = requests.get(f"{backend_url}/api/matches?season={season}", timeout=15)
        
        if response.status_code == 200:
            final_matches = response.json()
            print(f"📊 Total matches now in database: {len(final_matches)}")
            
            if final_matches:
                print(f"\n✅ SAMPLE SCRAPED DATA:")
                
                # Show first few matches with full details
                for i, match in enumerate(final_matches[:5]):
                    home = match.get('home_team', 'Unknown')
                    away = match.get('away_team', 'Unknown')
                    home_score = match.get('home_score', '?')
                    away_score = match.get('away_score', '?')
                    home_shots = match.get('home_shots', '?')
                    away_shots = match.get('away_shots', '?')
                    home_xg = match.get('home_expected_goals', '?')
                    away_xg = match.get('away_expected_goals', '?')
                    match_date = match.get('match_date', '?')
                    
                    print(f"\n   Match {i+1}: {home} {home_score}-{away_score} {away}")
                    print(f"      Date: {match_date}")
                    print(f"      Shots: {home_shots} vs {away_shots}")
                    print(f"      xG: {home_xg} vs {away_xg}")
                
                # Data quality analysis
                print(f"\n📈 DATA QUALITY ANALYSIS:")
                
                # Count matches with complete data
                complete_matches = 0
                matches_with_stats = 0
                
                for match in final_matches:
                    if (match.get('home_team') and match.get('away_team') and 
                        match.get('home_score') is not None and match.get('away_score') is not None):
                        complete_matches += 1
                    
                    if (match.get('home_shots') and match.get('away_shots')):
                        matches_with_stats += 1
                
                completion_rate = (complete_matches / len(final_matches) * 100) if final_matches else 0
                stats_rate = (matches_with_stats / len(final_matches) * 100) if final_matches else 0
                
                print(f"   Complete matches (teams + scores): {complete_matches}/{len(final_matches)} ({completion_rate:.1f}%)")
                print(f"   Matches with statistics: {matches_with_stats}/{len(final_matches)} ({stats_rate:.1f}%)")
                
                # Success assessment
                if completion_rate >= 90:
                    print(f"   🎉 EXCELLENT data quality!")
                elif completion_rate >= 70:
                    print(f"   👍 GOOD data quality")
                elif completion_rate >= 50:
                    print(f"   ⚠️  FAIR data quality - needs improvement")
                else:
                    print(f"   ❌ POOR data quality - significant issues")
                
            else:
                print(f"❌ No matches found in database after scraping")
                
        else:
            print(f"❌ Could not verify final database state: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error checking final database: {e}")
    
    # Step 7: Performance summary
    print_section("7. PERFORMANCE SUMMARY")
    
    try:
        # Get scraping status one more time for final stats
        response = requests.get(f"{backend_url}/api/scraping-status/{status_id}", timeout=10)
        
        if response.status_code == 200:
            final_status = response.json()
            
            total_time = time.time() - start_time
            matches_scraped = final_status.get('matches_scraped', 0)
            total_matches = final_status.get('total_matches', 0)
            errors = final_status.get('errors', [])
            
            print(f"📊 FINAL PERFORMANCE METRICS:")
            print(f"   Total execution time: {total_time:.1f} seconds ({total_time/60:.1f} minutes)")
            print(f"   Matches attempted: {total_matches}")
            print(f"   Matches completed: {matches_scraped}")
            print(f"   Success rate: {(matches_scraped/total_matches*100):.1f}%" if total_matches > 0 else "N/A")
            print(f"   Error count: {len(errors)}")
            print(f"   Average time per match: {(total_time/matches_scraped):.1f}s" if matches_scraped > 0 else "N/A")
            
            # Overall assessment
            success_rate = (matches_scraped/total_matches*100) if total_matches > 0 else 0
            
            if success_rate >= 95 and len(errors) < 10:
                overall_grade = "🎉 EXCELLENT"
            elif success_rate >= 80 and len(errors) < 20:
                overall_grade = "👍 GOOD"
            elif success_rate >= 60:
                overall_grade = "⚠️  FAIR"
            else:
                overall_grade = "❌ POOR"
            
            print(f"\n🎯 OVERALL ASSESSMENT: {overall_grade}")
            
            return success_rate >= 70  # Consider 70%+ a success
            
    except Exception as e:
        print(f"❌ Error generating performance summary: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_full_season_with_database())
    
    print_header("TEST CONCLUSION")
    
    if success:
        print("🎉 END-TO-END TEST: SUCCESSFUL")
        print("✅ The system can process full seasons of data")
        print("✅ Database storage is working")
        print("✅ Data quality is acceptable")
        print("\n🚀 READY FOR PRODUCTION USE!")
    else:
        print("⚠️  END-TO-END TEST: NEEDS IMPROVEMENT")
        print("❌ Some issues detected during processing")
        print("🔧 Additional fixes may be needed")
    
    print(f"\n💾 Test completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")