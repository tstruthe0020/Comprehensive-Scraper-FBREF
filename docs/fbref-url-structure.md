# FBref URL Structure Reference Guide

**Last Updated:** June 2, 2025  
**Status:** ✅ Verified Working  
**Browser Automation:** Playwright (ARM64 Compatible)

---

## 🎯 **OVERVIEW**

This document provides the complete URL structure for FBref.com Premier League data scraping. The URL patterns differ significantly between current and historical seasons, requiring dynamic URL construction based on date logic.

---

## 📋 **SEASON MANAGEMENT LOGIC**

### **Current vs Historical Season Determination**

```python
def _is_current_season(season: str, current_date) -> bool:
    """
    Current season logic:
    - 2024-25 is current until August 1, 2025
    - On August 1, 2025: 2025-26 becomes current, 2024-25 becomes historical
    - Pattern continues each year
    """
    year = current_date.year
    month = current_date.month
    
    if month >= 8:  # August or later - new season starts
        current_season = f"{year}-{str(year + 1)[2:]}"
    else:  # Before August - still in previous season
        current_season = f"{year - 1}-{str(year)[2:]}"
    
    return season == current_season
```

### **Season Format Conversion**

```python
def _convert_to_full_season_format(season: str) -> str:
    """
    Convert: "2023-24" → "2023-2024"
    FBref historical URLs require full YYYY-YYYY format
    """
    if '-' in season and len(season) == 7:  # Format: "2023-24"
        start_year = season[:4]
        start_year_int = int(start_year)
        end_year_full = str(start_year_int + 1)
        return f"{start_year}-{end_year_full}"
    return season
```

---

## 🔗 **URL PATTERNS**

### **1. Season Fixtures/Schedule Pages**

#### **Current Season (2024-25 as of June 2025)**
```
https://fbref.com/en/comps/9/schedule/Premier-League-Scores-and-Fixtures
```
- **Status:** ✅ Verified - 1147 match links found
- **Table ID:** `sched_2024-2025_9_1`
- **Features:** Live fixtures, ongoing season data

#### **Historical Seasons**
```
https://fbref.com/en/comps/9/{YYYY-YYYY}/schedule/{YYYY-YYYY}-Premier-League-Scores-and-Fixtures
```

**Examples:**
- **2023-24:** `https://fbref.com/en/comps/9/2023-2024/schedule/2023-2024-Premier-League-Scores-and-Fixtures`
  - ✅ Verified - 1198 match links found
  - Table ID: `sched_2023-2024_9_1`
  
- **2022-23:** `https://fbref.com/en/comps/9/2022-2023/schedule/2022-2023-Premier-League-Scores-and-Fixtures`
  - ✅ URL Pattern Verified
  - Table ID: `sched_2022-2023_9_1`

### **2. Individual Match Report Pages**

#### **URL Pattern (Same for All Seasons)**
```
https://fbref.com/en/matches/{match_id}/{team1-team2-date-Premier-League}
```

#### **Current Season Examples (2024-25)**
```
https://fbref.com/en/matches/9c4f2bcd/Brentford-West-Ham-United-September-28-2024-Premier-League
https://fbref.com/en/matches/eb58af0b/Southampton-Aston-Villa-April-12-2025-Premier-League
```

#### **Historical Season Examples**
```
# 2023-24
https://fbref.com/en/matches/4f754e0a/Brighton-and-Hove-Albion-Newcastle-United-September-2-2023-Premier-League

# 2022-23  
https://fbref.com/en/matches/c31cf944/Nottingham-Forest-Chelsea-January-1-2023-Premier-League
```

### **3. Season Index Page**
```
https://fbref.com/en/comps/9/history/Premier-League-Seasons
```
- **Purpose:** Lists all available Premier League seasons
- **Use Case:** Discovering available seasons for scraping

---

## 🧪 **TESTING RESULTS**

### **URL Validation Tests (June 2, 2025)**

| Season | URL Type | Status | Match Links | Table ID |
|--------|----------|--------|-------------|----------|
| 2024-25 (Current) | Fixtures | ✅ Working | 1147 | `sched_2024-2025_9_1` |
| 2023-24 (Historical) | Fixtures | ✅ Working | 1198 | `sched_2023-2024_9_1` |
| 2022-23 (Historical) | Fixtures | ✅ Pattern Verified | N/A | `sched_2022-2023_9_1` |

### **Playwright Compatibility**
- ✅ **ARM64 Support:** Full compatibility confirmed
- ✅ **Browser Management:** Automatic Chromium binary handling
- ✅ **Navigation Success:** All tested URLs load successfully
- ✅ **Data Extraction:** Match links successfully extracted

---

## 🔧 **IMPLEMENTATION REFERENCE**

### **Backend URL Construction Method**

```python
def get_season_fixtures_url(self, season: str) -> str:
    """Get the fixtures URL for a specific season with proper current/historical logic"""
    from datetime import datetime
    
    current_date = datetime.now()
    is_current_season = self._is_current_season(season, current_date)
    
    if is_current_season:
        # Current season uses simple URL without season in path
        return "https://fbref.com/en/comps/9/schedule/Premier-League-Scores-and-Fixtures"
    else:
        # Historical seasons use full season format (YYYY-YYYY)
        full_season = self._convert_to_full_season_format(season)
        return f"https://fbref.com/en/comps/9/{full_season}/schedule/{full_season}-Premier-League-Scores-and-Fixtures"
```

### **Usage Examples**

```python
# Current season (as of June 2025)
url_current = scraper.get_season_fixtures_url("2024-25")
# Returns: https://fbref.com/en/comps/9/schedule/Premier-League-Scores-and-Fixtures

# Historical season
url_historical = scraper.get_season_fixtures_url("2023-24")  
# Returns: https://fbref.com/en/comps/9/2023-2024/schedule/2023-2024-Premier-League-Scores-and-Fixtures
```

---

## 📅 **SEASON TRANSITION SCHEDULE**

| Date Range | Current Season | Historical Seasons |
|------------|----------------|-------------------|
| Until July 31, 2025 | 2024-25 | 2023-24, 2022-23, etc. |
| August 1, 2025+ | 2025-26 | 2024-25, 2023-24, etc. |
| August 1, 2026+ | 2026-27 | 2025-26, 2024-25, etc. |

---

## 🚨 **IMPORTANT NOTES**

### **URL Structure Differences**
1. **Current Season:** No season identifier in URL path
2. **Historical Seasons:** Full `YYYY-YYYY` format required in path and filename
3. **Match URLs:** Consistent format across all seasons

### **Browser Automation Requirements**
- **Playwright Required:** ChromeDriver has ARM64 compatibility issues
- **Headless Mode:** Recommended for server deployments
- **Network Stability:** Long-running scraping may require session management

### **Rate Limiting Considerations**
- **Respectful Delays:** 5-second delays between match requests recommended
- **Session Management:** Monitor for "Target page closed" errors on long runs
- **Error Handling:** Implement retry logic for network timeouts

---

## 🔄 **MAINTENANCE SCHEDULE**

- **Annual Review:** Verify URL patterns before each season (July)
- **Pattern Updates:** Check if FBref changes URL structure
- **Season Logic:** Update current season detection logic annually
- **Test Validation:** Run URL validation tests before major scraping operations

---

**This documentation ensures reliable FBref data extraction with proper URL management across current and historical Premier League seasons.**