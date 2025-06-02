#!/usr/bin/env python3
"""
Test the URL construction logic for different seasons
"""
from datetime import datetime

def get_season_fixtures_url(season: str) -> str:
    """Get the fixtures URL for a specific season with proper current/historical logic"""
    
    # Determine if season is current based on date
    current_date = datetime.now()
    is_current_season = _is_current_season(season, current_date)
    
    if is_current_season:
        # Current season uses simple URL without season in path
        return "https://fbref.com/en/comps/9/schedule/Premier-League-Scores-and-Fixtures"
    else:
        # Historical seasons use full season format (YYYY-YYYY)
        full_season = _convert_to_full_season_format(season)
        return f"https://fbref.com/en/comps/9/{full_season}/schedule/{full_season}-Premier-League-Scores-and-Fixtures"

def _is_current_season(season: str, current_date) -> bool:
    """Determine if a season is the current season based on date"""
    # Current season is 2024-25 until August 1, 2025
    # After August 1, 2025, 2025-26 becomes current, etc.
    
    year = current_date.year
    month = current_date.month
    
    if month >= 8:  # August or later - new season starts
        current_season = f"{year}-{str(year + 1)[2:]}"
    else:  # Before August - still in previous season
        current_season = f"{year - 1}-{str(year)[2:]}"
    
    return season == current_season

def _convert_to_full_season_format(season: str) -> str:
    """Convert season format from YYYY-YY to YYYY-YYYY"""
    # Convert "2023-24" to "2023-2024"
    if '-' in season and len(season) == 7:  # Format: "2023-24"
        start_year = season[:4]
        end_year_short = season[5:]
        
        # Convert short year to full year
        start_year_int = int(start_year)
        end_year_full = str(start_year_int + 1)
        
        return f"{start_year}-{end_year_full}"
    
    # If already in full format or different format, return as-is
    return season

def test_url_construction():
    """Test URL construction for various seasons"""
    print("🧪 Testing URL Construction Logic")
    print(f"📅 Current Date: {datetime.now().strftime('%Y-%m-%d')}")
    
    test_seasons = ["2024-25", "2023-24", "2022-23", "2021-22", "2025-26"]
    expected_urls = {
        "2024-25": "https://fbref.com/en/comps/9/schedule/Premier-League-Scores-and-Fixtures",
        "2023-24": "https://fbref.com/en/comps/9/2023-2024/schedule/2023-2024-Premier-League-Scores-and-Fixtures",
        "2022-23": "https://fbref.com/en/comps/9/2022-2023/schedule/2022-2023-Premier-League-Scores-and-Fixtures",
        "2021-22": "https://fbref.com/en/comps/9/2021-2022/schedule/2021-2022-Premier-League-Scores-and-Fixtures",
        "2025-26": "https://fbref.com/en/comps/9/2025-2026/schedule/2025-2026-Premier-League-Scores-and-Fixtures"
    }
    
    print("\n🔗 URL Generation Results:")
    for season in test_seasons:
        generated_url = get_season_fixtures_url(season)
        expected_url = expected_urls.get(season, "Unknown")
        
        is_current = _is_current_season(season, datetime.now())
        status = "✅ CURRENT" if is_current else "📚 HISTORICAL"
        match_status = "✅ MATCHES" if generated_url == expected_url else "❌ MISMATCH"
        
        print(f"\n📋 Season {season} ({status}):")
        print(f"   Generated: {generated_url}")
        print(f"   Expected:  {expected_url}")
        print(f"   Status:    {match_status}")

if __name__ == "__main__":
    test_url_construction()