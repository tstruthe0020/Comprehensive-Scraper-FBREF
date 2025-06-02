# Documentation Index

This directory contains comprehensive documentation for the FBref Analytics Platform.

## 📁 **Documentation Files**

### **`fbref-url-structure.md`**
- **Purpose:** Complete FBref URL patterns and season management logic
- **Contains:** Current vs historical season URL structures, testing results, implementation examples
- **Key Info:** Date-based season transitions (August 1st), URL format conversion logic

### **`CHANGELOG.md`**
- **Purpose:** Technical changelog documenting major system changes
- **Contains:** Playwright migration details, breaking changes, performance improvements
- **Key Info:** Browser automation migration from Selenium to Playwright

### **`TODO-match-report-scraping.md`** 🆕
- **Purpose:** Comprehensive to-do list for match report scraping implementation
- **Contains:** Critical issues, prioritized tasks, implementation checklist
- **Key Info:** Session management fixes, HTML structure analysis, data extraction tasks

## 🚨 **Current Priority Issues**

### **🔴 Critical (P0)**
1. **Browser session disconnection** during long scraping runs
2. **Unknown match report HTML structure** - need real FBref analysis
3. **Data extraction logic validation** - test against actual pages

### **🟡 High Priority (P1)**  
1. **Implement session recovery mechanisms**
2. **Map FBref HTML to data models** (80+ team fields, 75+ player fields)
3. **Add comprehensive error handling** and logging

### **🟢 Medium Priority (P2)**
1. **Single match report testing** and validation
2. **Large-scale scraping testing** (380+ matches)
3. **Database integration testing** with real data

## 🔗 **Quick Reference**

### **Current Season URL (2024-25)**
```
https://fbref.com/en/comps/9/schedule/Premier-League-Scores-and-Fixtures
```

### **Historical Season URL Pattern**
```
https://fbref.com/en/comps/9/{YYYY-YYYY}/schedule/{YYYY-YYYY}-Premier-League-Scores-and-Fixtures
```

### **Test Match Report URL**
```
https://fbref.com/en/matches/9c4f2bcd/Brentford-West-Ham-United-September-28-2024-Premier-League
```

### **Season Transition Logic**
- **Current until August 1st:** Each season remains "current" until August 1st of the following year
- **Example:** 2024-25 is current until August 1, 2025, then 2025-26 becomes current

## 🧰 **Implementation References**

### **Backend URL Construction**
```python
# See: /app/backend/server.py
def get_season_fixtures_url(self, season: str) -> str
def _is_current_season(self, season: str, current_date) -> bool  
def _convert_to_full_season_format(self, season: str) -> str
```

### **Browser Automation**
```python
# Playwright setup (ARM64 compatible)
from playwright.async_api import async_playwright
playwright = await async_playwright().start()
browser = await playwright.chromium.launch(headless=True)
```

### **Current Known Issues**
```python
# Session management error
ERROR: Page.goto: Target page, context or browser has been closed

# Rate limiting detection needed
ERROR: Page.goto: net::ERR_ABORTED

# Data extraction validation needed
# Current selectors may not work on real FBref pages
```

## 📊 **Verified Working URLs**

| Season | Type | Status | Match Links |
|--------|------|--------|-------------|
| 2024-25 | Current | ✅ Working | 1,147 |
| 2023-24 | Historical | ✅ Working | 1,198 |
| 2022-23 | Historical | ✅ Pattern Verified | N/A |

## 🎯 **Next Steps Priority**

1. **🔴 URGENT:** Analyze single match report HTML structure
2. **🔴 URGENT:** Fix browser session management for long-running scraping
3. **🟡 HIGH:** Implement real data extraction logic based on actual FBref structure
4. **🟡 HIGH:** Add comprehensive error handling and session recovery

---

**Last Updated:** June 2, 2025  
**Next Review:** Weekly until match report scraping is stable  
**Current Status:** 🔴 Critical issues blocking data extraction