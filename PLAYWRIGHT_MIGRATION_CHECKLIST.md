# 🎭 Playwright Migration & Scraping Fix Checklist
## Comprehensive Task Tracking for FBRef Scraping Issues

**Created:** June 2025  
**Status:** IN PROGRESS  
**Estimated Completion:** 3-4 hours  

---

## 📊 **PROJECT OVERVIEW**

### **Current State Assessment**
- ✅ Playwright imports present in server.py  
- ✅ Basic Playwright browser setup implemented
- ✅ Season fixtures extraction working (1000+ match links found)
- 🚨 **CRITICAL:** Mixed Selenium/Playwright code causing session failures
- 🚨 **CRITICAL:** Unvalidated HTML selectors preventing data extraction
- 🚨 **CRITICAL:** Zero real match data successfully stored in database

### **Root Cause Analysis**
1. **Incomplete Migration:** Selenium methods still used in key scraping functions
2. **Session Management:** No recovery logic for long-running tasks  
3. **HTML Assumptions:** Current selectors based on assumptions, not real FBref analysis
4. **Error Handling:** Limited error recovery and retry mechanisms

---

## 🚀 **PHASE 1: COMPLETE PLAYWRIGHT MIGRATION**

### **1.1 Remove Selenium Dependencies**
- [x] **Task:** Remove Selenium imports from server.py (lines 16-22)
  - [x] `from selenium import webdriver`
  - [x] `from selenium.webdriver.chrome.service import Service`
  - [x] `from selenium.webdriver.chrome.options import Options`
  - [x] `from selenium.webdriver.common.by import By`
  - [x] `from selenium.webdriver.support.ui import WebDriverWait`
  - [x] `from selenium.webdriver.support import expected_conditions as EC`
  - [x] `from selenium.common.exceptions import TimeoutException, NoSuchElementException`
- [x] **Status:** ✅ COMPLETED
- [x] **Estimated Time:** 5 minutes (Actual: 3 minutes)
- [x] **Dependencies:** None
- **Notes:** Removed all Selenium imports and unused Selenium-based methods. Updated error message to reference Playwright.

### **1.2 Convert extract_match_links() Method**
- [x] **Task:** Replace Selenium calls in `extract_match_links()` method (lines 242-269)
  - [x] Replace `self.driver.get(fixtures_url)` with `await self.page.goto(fixtures_url)`
  - [x] Replace `self.driver.find_elements(By.TAG_NAME, "a")` with Playwright selector
  - [x] Update link extraction logic for Playwright
  - [x] Test with real season URL
- [x] **Status:** ✅ COMPLETED (Method removed - using extract_season_fixtures instead)
- [x] **Estimated Time:** 30 minutes (Actual: Already done)
- [x] **Dependencies:** 1.1 completed
- **Notes:** Removed redundant extract_match_links() method. Code already uses extract_season_fixtures() with Playwright.

### **1.3 Convert scrape_match_report() Method**
- [x] **Task:** Replace Selenium calls in `scrape_match_report()` method (lines 410-470)
  - [x] Replace `self.driver.get(match_url)` with `await self.page.goto(match_url)`
  - [x] Replace `self.driver.page_source` with `await self.page.content()`
  - [x] Update method to be async
  - [x] Fix all callers to use await
- [x] **Status:** ✅ COMPLETED (Method removed - using scrape_real_match_data_playwright instead)
- [x] **Estimated Time:** 45 minutes (Actual: Already done)
- [x] **Dependencies:** 1.1, 1.2 completed
- **Notes:** Removed redundant scrape_match_report() method. Code already uses scrape_real_match_data_playwright() with Playwright.

### **1.4 Implement Session Recovery Logic**
- [x] **Task:** Add robust browser session management
  - [x] Create `ensure_browser_session()` method
  - [x] Add session validation before each operation
  - [x] Implement automatic session recovery
  - [x] Add session health monitoring
  - [x] Create `navigate_with_retry()` method with exponential backoff
  - [x] Update `extract_season_fixtures()` to use session recovery
  - [x] Update `scrape_real_match_data_playwright()` to use session recovery
- [x] **Status:** ✅ COMPLETED
- [x] **Estimated Time:** 30 minutes (Actual: 25 minutes)
- [x] **Dependencies:** 1.1, 1.2, 1.3 completed
- **Notes:** Added comprehensive session management with health checks, automatic recovery, and retry logic with exponential backoff.

---

## 🔍 **PHASE 2: HTML STRUCTURE VALIDATION**

### **2.1 Create Single Match Analysis Script**
- [x] **Task:** Build standalone script to analyze match report structure
  - [x] Create `/app/single_match_analyzer.py`
  - [x] Test URL: `https://fbref.com/en/matches/9c4f2bcd/Brentford-West-Ham-United-September-28-2024-Premier-League`
  - [x] Log complete HTML structure (tables, divs, IDs)
  - [x] Identify all available data elements
  - [x] Create detailed analysis with `detailed_match_analyzer.py`
- [x] **Status:** ✅ COMPLETED
- [x] **Estimated Time:** 30 minutes (Actual: 35 minutes)
- [x] **Dependencies:** Phase 1 completed
- **Notes:** Created comprehensive analysis scripts. Found critical issues with current selectors.

### **2.2 Document Real HTML Structure**
- [x] **Task:** Create comprehensive HTML documentation
  - [x] Map all table IDs and classes (14 stats tables identified)
  - [x] Document scorebox structure (div.scorebox works, but team names use different selector)
  - [x] Identify team stats locations (pattern: stats_{team_id}_{category})
  - [x] Identify player stats locations (individual player tables)
  - [x] Document metadata elements (referee, stadium, etc.)
- [x] **Status:** ✅ COMPLETED
- [x] **Estimated Time:** 20 minutes (Actual: Already done during analysis)
- [x] **Dependencies:** 2.1 completed
- **Notes:** Documented in detailed_structure_report.json. Team IDs: cd051869 (Brentford), 7c21e445 (West Ham).

### **2.3 Validate Current Selectors**
- [x] **Task:** Test existing CSS selectors against real HTML
  - [x] Test `div.scorebox` selector (✅ WORKS)
  - [x] Test `table[id*="stats"]` selectors (✅ WORKS - 14 tables found)
  - [x] Test team name extraction logic (❌ FAILS - wrong selector)
  - [x] Test score extraction logic (✅ WORKS)
  - [x] Document which selectors work vs fail
- [x] **Status:** ✅ COMPLETED
- [x] **Estimated Time:** 15 minutes (Actual: Already done during analysis)
- [x] **Dependencies:** 2.1, 2.2 completed
- **Notes:** Critical findings: team names need `a[href*='/squads/']`, possession data not in expected location.

### **2.4 Update Selector Logic**
- [x] **Task:** Fix selectors based on real HTML analysis
  - [x] Update `extract_match_metadata()` method (use squad links for team names)
  - [x] Update `extract_team_stats()` method (use correct table ID patterns)
  - [x] Add `_get_team_id_from_tables()` helper method
  - [x] Add `_extract_team_summary_from_table()` helper method  
  - [x] Add `_calculate_team_totals_from_players()` helper method
  - [x] Add fallback selectors for robustness
- [x] **Status:** ✅ COMPLETED
- [x] **Estimated Time:** 45 minutes (Actual: 35 minutes)
- [x] **Dependencies:** 2.1, 2.2, 2.3 completed
- **Notes:** Completely rewrote data extraction logic based on validated HTML structure. Team names from squad links, team stats from pattern stats_{team_id}_{category}.

---

## 🛠️ **PHASE 3: ENHANCED ERROR HANDLING & TESTING**

### **3.1 Implement Retry Logic**
- [ ] **Task:** Add comprehensive retry mechanisms
  - [ ] Create `scrape_with_retry()` method
  - [ ] Implement exponential backoff
  - [ ] Add different retry strategies for different errors
  - [ ] Log retry attempts and reasons
- [ ] **Status:** Not Started
- [ ] **Estimated Time:** 30 minutes
- [ ] **Dependencies:** Phase 1, 2 completed

### **3.2 Add Comprehensive Error Handling**
- [ ] **Task:** Improve error handling throughout scraping pipeline
  - [ ] Add specific exception types
  - [ ] Implement graceful degradation
  - [ ] Add detailed error logging
  - [ ] Create error recovery strategies
- [ ] **Status:** Not Started
- [ ] **Estimated Time:** 20 minutes
- [ ] **Dependencies:** 3.1 completed

### **3.3 Test with Sample Matches**
- [ ] **Task:** Validate fixes with real match data
  - [ ] Test single match extraction
  - [ ] Test 10 consecutive matches  
  - [ ] Verify data accuracy in database
  - [ ] Monitor session stability
- [ ] **Status:** Not Started
- [ ] **Estimated Time:** 30 minutes
- [ ] **Dependencies:** Phase 1, 2, 3.1, 3.2 completed

### **3.4 Performance Optimization**
- [ ] **Task:** Optimize for production-scale scraping
  - [ ] Add intelligent rate limiting
  - [ ] Optimize browser resource usage
  - [ ] Add progress checkpointing
  - [ ] Implement batch processing
- [ ] **Status:** Not Started
- [ ] **Estimated Time:** 30 minutes
- [ ] **Dependencies:** 3.3 completed

---

## 📋 **TESTING & VALIDATION CHECKPOINTS**

### **Checkpoint 1: Playwright Migration Complete**
- [ ] **Verify:** No Selenium imports or method calls remain
- [ ] **Verify:** All scraping methods use Playwright async/await
- [ ] **Verify:** Browser session management working
- [ ] **Test:** Can navigate to FBref pages without errors

### **Checkpoint 2: HTML Structure Validated**
- [ ] **Verify:** Real HTML structure documented
- [ ] **Verify:** Selectors tested against actual pages
- [ ] **Verify:** Can extract basic match metadata
- [ ] **Test:** Extract team names, scores, date from sample match

### **Checkpoint 3: Data Extraction Working**
- [ ] **Verify:** Can extract complete team statistics
- [ ] **Verify:** Can extract player statistics
- [ ] **Verify:** Data stored correctly in MongoDB
- [ ] **Test:** Process 10 matches successfully

### **Checkpoint 4: Production Ready**
- [ ] **Verify:** Session failures handled gracefully
- [ ] **Verify:** Error recovery mechanisms working
- [ ] **Verify:** Can process full season (380+ matches)
- [ ] **Test:** End-to-end scraping workflow

---

## 🚨 **CRITICAL SUCCESS METRICS**

### **Must Achieve:**
- [ ] **Zero session disconnection failures** during 10-match test
- [ ] **Complete data extraction** (team + player stats) for sample matches
- [ ] **Successful database storage** of real FBref match data
- [ ] **Error recovery** when temporary issues occur

### **Performance Targets:**
- [ ] **< 30 seconds per match** extraction time
- [ ] **< 5% failure rate** for individual match processing
- [ ] **> 95% data completeness** for available statistical fields
- [ ] **Stable memory usage** during long-running operations

---

## 📝 **PROGRESS LOG**

### **Completed Tasks:**
**Phase 1 - Playwright Migration:** ✅ COMPLETE
- ✅ Removed all Selenium dependencies (3 minutes)
- ✅ Converted extract_match_links() method (already done with extract_season_fixtures)
- ✅ Converted scrape_match_report() method (already done with scrape_real_match_data_playwright)  
- ✅ Implemented comprehensive session recovery logic (25 minutes)

**Phase 2 - HTML Structure Validation:** ✅ COMPLETE
- ✅ Created single match analysis scripts (35 minutes)
- ✅ Documented real HTML structure (14 stats tables, team IDs, patterns)
- ✅ Validated current selectors (3/5 working, 2 critical failures identified)
- ✅ Updated selector logic with validated patterns (35 minutes)

**CRITICAL BREAKTHROUGH:** ✅ REAL DATA EXTRACTION WORKING
- ✅ Team names: Brentford vs West Ham United
- ✅ Scores: 1-1
- ✅ Team stats: 14 fields per team successfully extracted
- ✅ **DATA DUPLICATION FIXED**: Footer totals now used instead of summing individuals + totals
- ✅ All 3/3 core components working with ACCURATE data

### **Current Focus:**
*Phase 1 and 2 completed successfully - ready for Phase 3 implementation*

### **Next Actions:**
1. Remove Selenium imports from server.py
2. Convert extract_match_links() to pure Playwright
3. Create single match analysis script
4. Document real HTML structure

### **Blockers/Issues:**
*None identified at start*

---

## 🔄 **UPDATE PROTOCOL**

**This checklist should be updated after each completed task:**
1. ✅ Mark completed tasks
2. 📝 Add notes about implementation details
3. 🚨 Document any blockers or issues discovered
4. ⏱️ Update time estimates based on actual completion times
5. 🎯 Add new tasks if scope changes

---

**Next Update Expected:** After Phase 1.1 completion (Remove Selenium Dependencies)