# 🚀 FBREF COMPREHENSIVE SCRAPER - DEBUGGING DOCUMENTATION

## 📋 PROJECT STATUS

### ✅ **WORKING COMPONENTS:**
- **Multi-season URL extraction** - Successfully extracts 760+ match URLs from Premier League seasons
- **Excel generation** - Creates structured Excel files with individual sheets per match
- **Playwright integration** - Bypasses FBREF anti-bot protection using Firefox
- **Real demo data** - Demo now pulls 5 real matches from current Premier League season
- **Enhancement infrastructure** - Backend API endpoints for Excel enhancement working
- **Data processor framework** - Updated with correct FBREF data-stat attribute names

### ⚠️ **CURRENT ISSUE:**
- **Data extraction**: Scraper finds 12 tables per match but extracts "0 data points"
- **Root cause**: `data-stat` attributes not being properly extracted from table cells
- **Impact**: Excel sheets get populated with empty values instead of real statistics

---

## 🏗️ **ARCHITECTURE OVERVIEW**

### **Backend Components:**
```
/app/backend/server.py                 # Main FastAPI server
/app/integration_wrapper.py           # Integration interface
/app/batch_scraper/                   # Comprehensive scraper system
├── fbref_batch_scraper.py           # Main scraper (Playwright-based)
├── data_processor.py                # Data processing with correct field names
├── excel_integrator.py              # Excel population logic
├── config.py                        # Configuration settings
└── requirements.txt                 # Dependencies
```

### **Frontend Components:**
```
/app/frontend/src/App.js              # React frontend with enhancement UI
/app/frontend/src/App.css             # Styling
```

---

## 🔧 **KEY FILES TO DEBUG**

### **1. Main Scraper (`/app/batch_scraper/fbref_batch_scraper.py`)**
- **Function**: `extract_table_rows()` (lines 197-230)
- **Issue**: `data-stat` attributes returning empty strings
- **Current behavior**: `"data_stat": ""` instead of `"data_stat": "poss"`

### **2. Data Processor (`/app/batch_scraper/data_processor.py`)**
- **Status**: ✅ Updated with correct FBREF field names
- **Key fields**: `'poss'`, `'shots'`, `'shots_on_target'`, `'cards_yellow'`, etc.
- **Functions**: `extract_team_summary()`, `extract_player_stats()`

### **3. Excel Integrator (`/app/batch_scraper/excel_integrator.py`)**
- **Status**: ✅ Updated to use correct data-stat mappings
- **Function**: `populate_team_stats_section()` - maps Excel fields to FBREF data-stat names

---

## 🧪 **DEBUGGING TOOLS**

### **Debug Script (`/app/debug_scraper.py`)**
```bash
cd /app && python debug_scraper.py
```
**Output files:**
- `/app/debug_raw_data.json` - Raw extracted data
- `/app/debug_processed_data.json` - Processed data

### **Test Enhancement:**
```bash
demo_excel=$(curl -s -X POST http://localhost:8001/api/demo-scrape | jq -r '.excel_data')
curl -X POST http://localhost:8001/api/enhance-excel \
  -H "Content-Type: application/json" \
  -d "{\"excel_data\": \"$demo_excel\", \"filename\": \"test.xlsx\"}" | jq .
```

### **Check Logs:**
```bash
tail -n 20 /var/log/supervisor/backend.*.log
```

---

## 🎯 **EXACT ISSUE TO SOLVE**

### **Problem Statement:**
The scraper correctly:
1. ✅ Navigates to FBREF match pages
2. ✅ Finds 12 tables per match
3. ✅ Extracts cell text content
4. ❌ **BUT**: `data-stat` attributes are empty (`""`)

### **Expected vs Actual:**
```javascript
// EXPECTED:
{
  "text": "65%",
  "data_stat": "poss"      // ← Should be possession stat
}

// ACTUAL:
{
  "text": "65%", 
  "data_stat": ""          // ← Empty string
}
```

### **Debug Evidence:**
From `/app/debug_raw_data.json`:
- `"total_tables_found": 12` ✅
- `"total_data_points": 0` ❌
- `"data_stat_values": {}` ❌ (empty)

---

## 🔍 **DEBUGGING STEPS**

### **Step 1: Verify Data-Stat Extraction**
Check if FBREF actually uses `data-stat` attributes:
```bash
cd /app && python -c "
import asyncio
from batch_scraper.fbref_batch_scraper import FBrefBatchScraper
from batch_scraper.config import Config

async def test():
    scraper = FBrefBatchScraper(Config())
    await scraper.setup_browser()
    await scraper.page.goto('https://fbref.com/en/matches/cc5b4244/Manchester-United-Fulham-August-16-2024-Premier-League')
    
    # Check if data-stat attributes exist
    data_stat_elements = await scraper.page.query_selector_all('[data-stat]')
    print(f'Found {len(data_stat_elements)} elements with data-stat')
    
    # Sample a few
    for i, elem in enumerate(data_stat_elements[:5]):
        data_stat = await elem.get_attribute('data-stat')
        text = await elem.text_content()
        print(f'{i}: data-stat={data_stat}, text={text}')
    
    await scraper.cleanup()

asyncio.run(test())
"
```

### **Step 2: Alternative Data Extraction**
If `data-stat` doesn't exist, try:
```python
# Look for table IDs/classes that contain stats
table_stats = await scraper.page.query_selector_all('table[id*="stats"], table[class*="stats"]')

# Or extract based on table position/headers
stats_tables = await scraper.page.evaluate('''
() => {
    const tables = Array.from(document.querySelectorAll('table'));
    return tables.map((table, i) => ({
        index: i,
        id: table.id,
        class: table.className,
        headerText: table.querySelector('thead tr')?.textContent?.trim()
    }));
}
''')
```

### **Step 3: Header-Based Extraction**
If data-stat fails, use column headers:
```python
# Extract by matching column headers to known stats
headers = ['Possession', 'Shots', 'SoT', 'Fouls', 'Cards']
# Map to table columns and extract data by position
```

---

## 🚀 **NEXT SESSION STARTUP**

### **Environment Setup:**
```bash
cd /app
sudo supervisorctl restart backend
curl http://localhost:8001/api/health  # Verify backend
```

### **Quick Test:**
```bash
# Test demo extraction
curl -X POST http://localhost:8001/api/demo-scrape | jq .success

# Test enhancement availability  
curl http://localhost:8001/api/check-enhancement | jq .available
```

### **Debug Current Issue:**
```bash
cd /app && python debug_scraper.py
cat /app/debug_raw_data.json | jq '.all_tables.table_11.rows[0]'
```

---

## 📊 **TARGET DATA STRUCTURE**

### **Team Stats We Need:**
```javascript
{
  "poss": "65%",           // Possession
  "shots": "15",           // Total Shots  
  "shots_on_target": "7",  // Shots on Target
  "corners": "8",          // Corner Kicks
  "fouls": "12",           // Fouls
  "cards_yellow": "3",     // Yellow Cards
  "cards_red": "0"         // Red Cards
}
```

### **Player Stats We Need:**
```javascript
{
  "player_name": "Bruno Fernandes",
  "minutes": "90",
  "goals": "0", 
  "assists": "1",
  "shots_total": "3",
  "passes_completed": "45"
}
```

---

## 🎯 **SUCCESS CRITERIA**

### **When Fixed:**
1. **Debug output shows**: `"total_data_points": 50+` (not 0)
2. **data_stat_values populated**: `{"poss": "65%", "shots": "15"}`
3. **Excel enhancement works**: Real statistics populate cells
4. **Team stats accurate**: Match FBREF website values
5. **Player stats complete**: All players listed with performance data

### **Validation Method:**
1. Run enhancement on demo data
2. Download enhanced Excel
3. Compare values to actual FBREF match page
4. Verify all statistical categories populated

---

## 🚨 **CRITICAL FILES - DO NOT MODIFY**
- `/app/frontend/.env` - React backend URL
- `/app/backend/.env` - MongoDB connection  
- `/app/backend/server.py` - Excel structure (rows 4, 12, 20, 29, 38)

---

## 📞 **CONTINUATION COMMAND**
```bash
# Start debugging session:
cd /app && python debug_scraper.py && echo "Check data extraction in debug files"
```

**🎯 FOCUS: Fix `data-stat` attribute extraction in `fbref_batch_scraper.py` to populate Excel with real statistics!**