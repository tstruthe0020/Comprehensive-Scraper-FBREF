# 🔧 FBREF SCRAPER - QUICK START GUIDE

## ⚡ **IMMEDIATE DEBUGGING (5 MINUTES)**

### **1. Check Current State:**
```bash
cd /app
sudo supervisorctl restart backend
curl http://localhost:8001/api/health
```

### **2. Run Debug Script:**
```bash
python debug_scraper.py
```

### **3. Check Data Extraction:**
```bash
# See what data is actually extracted
cat debug_raw_data.json | jq '.metadata'
cat debug_raw_data.json | jq '.all_tables.table_11.rows[0].data_stat_values'
```

**Expected**: `{}` (empty) ← **THIS IS THE PROBLEM**  
**Needed**: `{"poss": "65%", "shots": "15"}` ← **THIS IS THE GOAL**

---

## 🎯 **THE ONE THING TO FIX**

**File**: `/app/batch_scraper/fbref_batch_scraper.py`  
**Function**: `extract_table_rows()` (line 197)  
**Issue**: `data-stat` attributes returning empty strings

### **Current Code (NOT WORKING):**
```python
cell_data = {
    'text': (await cell.text_content()).strip(),
    'data_stat': await cell.get_attribute("data-stat") or ""  # ← Returns ""
}
```

### **Need to Try:**
1. **Different attribute names**: `data-stat`, `data_stat`, `stat`
2. **JavaScript extraction**: Use `evaluate()` to get attributes  
3. **Header-based mapping**: Map by column position instead of attributes

---

## 🚀 **TEST ENHANCEMENT**
```bash
# Test with real data
demo_excel=$(curl -s -X POST http://localhost:8001/api/demo-scrape | jq -r '.excel_data')
curl -X POST http://localhost:8001/api/enhance-excel \
  -H "Content-Type: application/json" \
  -d "{\"excel_data\": \"$demo_excel\", \"filename\": \"test.xlsx\"}" \
  --max-time 300 | jq '{success, message}'
```

---

## ✅ **VALIDATION**
When working, debug output should show:
- `"total_data_points": 50+` (not 0)
- `"data_stat_values": {"poss": "65%"}` (not empty)

**🎯 GOAL: Get real FBREF statistics into Excel cells!**