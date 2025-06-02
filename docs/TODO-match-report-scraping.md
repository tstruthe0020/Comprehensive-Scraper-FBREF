# Match Report Scraping - To-Do List

**Created:** June 2, 2025  
**Status:** 🔴 Critical Issues Identified  
**Priority:** High - Core functionality blocked

---

## 🚨 **CRITICAL ISSUES (Immediate Action Required)**

### **P0 - Session Management Failures**
- [ ] **Fix browser session disconnection during long scraping runs**
  - **Issue:** `Page.goto: Target page, context or browser has been closed`
  - **Impact:** Scraping stops mid-process, no data stored despite finding 380+ fixtures
  - **Current:** Sessions close after ~5-10 match requests
  - **Needed:** Session recovery and retry mechanisms

- [ ] **Implement browser session recovery logic**
  ```python
  async def ensure_browser_session(self):
      if not self.browser or self.browser.is_closed():
          await self.setup_browser()
  ```

- [ ] **Add retry mechanism for failed requests**
  ```python
  async def scrape_with_retry(self, url, max_retries=3):
      # Implement exponential backoff and session recovery
  ```

### **P0 - Unknown Match Report HTML Structure**
- [ ] **Analyze actual FBref match report page structure**
  - **Test URL:** `https://fbref.com/en/matches/9c4f2bcd/Brentford-West-Ham-United-September-28-2024-Premier-League`
  - **Goal:** Document real HTML elements, table IDs, CSS classes
  - **Current:** Using assumed selectors that may not work

- [ ] **Create match report structure documentation**
  - [ ] Document all table structures and IDs
  - [ ] Map team stats table layouts
  - [ ] Map player stats table layouts  
  - [ ] Document scorebox and metadata elements

- [ ] **Validate current parsing logic against real pages**
  - [ ] Test scorebox extraction: `soup.find('div', class_='scorebox')`
  - [ ] Test stats table finding: `table[id*="stats"]`
  - [ ] Test team/player data extraction logic

---

## 🔧 **HIGH PRIORITY FIXES**

### **P1 - Data Extraction Implementation**
- [ ] **Map FBref HTML to our data models**
  - [ ] Team stats (80+ fields) → `TeamMatchData` model
  - [ ] Player stats (75+ fields) → `PlayerMatchData` model
  - [ ] Match metadata → referee, stadium, date fields

- [ ] **Implement robust team statistics extraction**
  ```python
  async def extract_team_stats_from_real_html(self, soup, team_name):
      # Based on actual FBref structure analysis
  ```

- [ ] **Implement robust player statistics extraction**
  ```python
  async def extract_player_stats_from_real_html(self, soup, team_name):
      # Based on actual FBref structure analysis
  ```

- [ ] **Handle missing or incomplete data gracefully**
  - [ ] Default values for missing statistics
  - [ ] Validation of extracted numeric values
  - [ ] Error handling for malformed data

### **P1 - Error Handling & Resilience**
- [ ] **Implement FBref-specific error detection**
  ```python
  # Detect rate limiting responses
  if "Rate limit" in response.text or response.status == 429:
      await implement_backoff_strategy()
  
  # Detect maintenance pages
  if "maintenance" in response.text.lower():
      raise TemporaryMaintenanceError()
  
  # Detect invalid match URLs
  if "Match not found" in response.text:
      logger.warning(f"Match not found: {url}")
      return None
  ```

- [ ] **Add comprehensive logging for debugging**
  ```python
  logger.info(f"Processing match: {url}")
  logger.info(f"Found tables: {[t.get('id') for t in tables]}")
  logger.info(f"Extracted scores: {home_score}-{away_score}")
  logger.info(f"Team stats fields extracted: {len(team_stats)}")
  logger.info(f"Player records extracted: {len(player_stats)}")
  ```

- [ ] **Implement progress saving and resume capability**
  - [ ] Save progress after each successful match
  - [ ] Resume from last processed match after failure
  - [ ] Skip already processed matches in database

---

## 🧪 **TESTING & VALIDATION TASKS**

### **P2 - Single Match Report Testing**
- [ ] **Create isolated match report test script**
  ```python
  # Test single match URL without full scraping pipeline
  # Log all discovered HTML elements
  # Validate data extraction accuracy
  ```

- [ ] **Test different match types**
  - [ ] Current season matches (2024-25)
  - [ ] Historical season matches (2023-24)
  - [ ] High-scoring matches (more player substitutions)
  - [ ] Matches with red cards/unusual events

- [ ] **Validate extracted data accuracy**
  - [ ] Compare extracted scores with known results
  - [ ] Verify team names match expected format
  - [ ] Check player statistics make sense (minutes ≤ 90, etc.)

### **P2 - Large-scale Scraping Testing**
- [ ] **Test processing 10-20 matches without session failures**
  - [ ] Monitor memory usage and browser resources
  - [ ] Test session recovery mechanisms
  - [ ] Validate database storage performance

- [ ] **Test rate limiting behavior**
  - [ ] Determine optimal delay between requests
  - [ ] Test FBref's rate limiting thresholds
  - [ ] Implement adaptive delay based on response times

- [ ] **Test different seasons and URL patterns**
  - [ ] Verify current season URLs work: 2024-25
  - [ ] Verify historical season URLs work: 2023-24, 2022-23
  - [ ] Test edge cases (postponed matches, rescheduled games)

---

## 📊 **DATA MODEL & DATABASE TASKS**

### **P2 - Database Integration**
- [ ] **Test real data storage in MongoDB**
  - [ ] Verify TeamMatchData model stores correctly
  - [ ] Verify PlayerMatchData model stores correctly
  - [ ] Test database query performance with real data

- [ ] **Add data validation constraints**
  ```python
  # Validate score ranges (0-10 realistic)
  # Validate minutes played (0-120 including extra time)
  # Validate possession percentages (0-100)
  # Validate team names against known Premier League teams
  ```

- [ ] **Implement duplicate detection**
  - [ ] Prevent storing same match multiple times
  - [ ] Handle re-scraping of updated match data
  - [ ] Add unique constraints for match identification

### **P3 - Advanced Data Processing**
- [ ] **Calculate additional metrics**
  - [ ] Passing accuracy percentages
  - [ ] Expected goals (xG) processing
  - [ ] Advanced possession metrics

- [ ] **Data quality validation**
  - [ ] Cross-validate team stats (both teams' possession = 100%)
  - [ ] Validate player minutes vs match duration
  - [ ] Flag suspicious or outlier statistics

---

## 🚀 **PERFORMANCE & OPTIMIZATION TASKS**

### **P3 - Session Management Optimization**
- [ ] **Implement browser pool for parallel processing**
  ```python
  # Multiple browser instances for faster scraping
  # Load balancing across browser sessions
  # Resource management and cleanup
  ```

- [ ] **Optimize browser settings for scraping**
  - [ ] Disable images and CSS for faster loading
  - [ ] Optimize viewport and memory settings
  - [ ] Test headless vs headed performance

- [ ] **Implement intelligent rate limiting**
  ```python
  # Adaptive delays based on response times
  # Backoff strategy for rate limit detection
  # Peak/off-peak hour optimization
  ```

### **P3 - Database Performance**
- [ ] **Optimize database writes**
  - [ ] Batch insert operations for multiple matches
  - [ ] Index optimization for common queries
  - [ ] Connection pooling for concurrent writes

- [ ] **Add monitoring and metrics**
  - [ ] Track scraping success rates
  - [ ] Monitor average processing time per match
  - [ ] Database storage and query performance metrics

---

## 📋 **IMPLEMENTATION CHECKLIST**

### **Phase 1: Critical Fixes (Week 1)**
- [ ] Create single match report analysis script
- [ ] Document actual FBref HTML structure  
- [ ] Implement session recovery mechanism
- [ ] Add comprehensive error handling and logging

### **Phase 2: Data Extraction (Week 2)**
- [ ] Implement real team stats extraction
- [ ] Implement real player stats extraction
- [ ] Test with 10-20 match sample
- [ ] Validate data accuracy and completeness

### **Phase 3: Scale & Optimize (Week 3)**
- [ ] Test full season scraping (380+ matches)
- [ ] Optimize rate limiting and performance
- [ ] Implement progress saving and resume
- [ ] Production readiness testing

---

## 🔍 **DEBUGGING PRIORITIES**

### **Immediate Investigation Needed**
1. **Why do browser sessions close during long scraping?**
   - Memory leaks in Playwright sessions?
   - FBref detecting automation and terminating connections?
   - Network timeouts causing session drops?

2. **What is the actual HTML structure of FBref match reports?**
   - Test with real match URL: analysis needed
   - Document all table IDs and CSS classes
   - Map data locations to our extraction logic

3. **Are our current CSS selectors correct?**
   - `div.scorebox` for match scores
   - `table[id*="stats"]` for statistics tables
   - Team and player identification logic

### **Error Pattern Analysis**
- [ ] Collect and analyze all scraping error logs
- [ ] Identify patterns in session failures
- [ ] Document specific FBref response patterns
- [ ] Create error categorization and handling matrix

---

## 📝 **DOCUMENTATION TASKS**

### **Technical Documentation**
- [ ] Update `/docs/fbref-url-structure.md` with match report findings
- [ ] Create `/docs/match-report-structure.md` for HTML analysis
- [ ] Document session management best practices
- [ ] Create troubleshooting guide for common errors

### **Code Documentation**
- [ ] Add comprehensive docstrings to all scraping methods
- [ ] Document data model field mappings
- [ ] Add inline comments for complex parsing logic
- [ ] Create example usage and testing scripts

---

**🎯 SUCCESS CRITERIA:**
- [ ] Successfully scrape 10 consecutive matches without session failures
- [ ] Extract and store complete team and player statistics in database
- [ ] Handle errors gracefully with recovery mechanisms
- [ ] Process full season (380+ matches) reliably
- [ ] Validate data accuracy against known match results

**📊 METRICS TO TRACK:**
- Session failure rate (target: <5%)
- Data extraction completeness (target: >95% of available fields)  
- Scraping speed (target: <30 seconds per match)
- Error recovery success rate (target: >90%)

---

*This to-do list should be updated as issues are resolved and new challenges are discovered during implementation.*