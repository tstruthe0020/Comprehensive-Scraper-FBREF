# 🚀 **FBREF BATCH SCRAPER**

## **📋 OVERVIEW**

This comprehensive batch scraping system reads Match Report URLs from a CSV file and extracts **ALL available data** from FBref match report pages, organizing it into clean, analyzable CSV files.

---

## **🎯 FEATURES**

### **✅ Comprehensive Data Extraction:**
- **Basic Match Info** - Teams, scores, date, stadium, referee
- **Team Summary Stats** - Possession, shots, xG, fouls, cards
- **Detailed Passing Stats** - Completion %, short/medium/long passes, key passes
- **Defensive Statistics** - Tackles, blocks, interceptions, clearances
- **Player Statistics** - Individual player performance data
- **Match Events** - Goals, cards, substitutions timeline
- **Raw Data** - Complete comprehensive extraction for future analysis

### **✅ Organized Output:**
- Multiple CSV files for different data types
- JSON file with complete raw data
- Error logging and summary reports
- Progress tracking and rate limiting

---

## **📦 INSTALLATION**

```bash
# Install dependencies
cd /app/batch_scraper
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium
```

---

## **🚀 USAGE**

### **Basic Usage:**
```bash
python fbref_batch_scraper.py --input example_input.csv --output results/
```

### **Advanced Usage:**
```bash
python fbref_batch_scraper.py \
    --input season_2024_25.csv \
    --output data/2024-25/ \
    --season 2024-25 \
    --url-column match_report_url
```

### **Command Line Arguments:**
- `--input` - Input CSV file with match URLs (required)
- `--output` - Output directory for results (required)
- `--season` - Season identifier (default: '2024-25')
- `--url-column` - Column name containing URLs (default: 'match_url')

---

## **📂 INPUT FORMAT**

Your CSV file should contain Match Report URLs:

```csv
match_url,date,home_team,away_team
https://fbref.com/en/matches/abc123/Arsenal-Chelsea-March-15-2024-Premier-League,2024-03-15,Arsenal,Chelsea
https://fbref.com/en/matches/def456/Liverpool-Manchester-City-April-20-2024-Premier-League,2024-04-20,Liverpool,Manchester City
```

**Required Column:**
- `match_url` (or specify custom column with `--url-column`)

**Optional Columns:**
- Any additional columns for your reference (preserved in match info)

---

## **📊 OUTPUT FILES**

The scraper generates multiple organized CSV files:

```
results/
├── 2024-25_match_info.csv          # Basic match information
├── 2024-25_team_summary.csv        # Team summary statistics  
├── 2024-25_passing_stats.csv       # Detailed passing statistics
├── 2024-25_defensive_stats.csv     # Defensive statistics
├── 2024-25_player_stats.csv        # Individual player statistics
├── 2024-25_match_events.csv        # Match events and timeline
├── 2024-25_raw_data.json          # Complete raw data
├── 2024-25_errors.csv             # Failed extractions
├── 2024-25_scraping_summary.csv   # Summary report
└── batch_scraper.log              # Detailed logs
```

### **📋 File Descriptions:**

#### **1. Match Info (`*_match_info.csv`)**
```csv
match_url,page_title,home_team,away_team,home_score,away_score,match_date,stadium,referee,attendance
```

#### **2. Team Summary (`*_team_summary.csv`)**
```csv
match_url,team,possession,shots_total,shots_on_target,expected_goals,passes_completed,passes_pct,fouls,cards_yellow,cards_red
```

#### **3. Passing Stats (`*_passing_stats.csv`)**
```csv
match_url,team,passes_completed,passes,passes_pct,passes_short_completed,passes_medium_completed,passes_long_completed,key_passes
```

#### **4. Defensive Stats (`*_defensive_stats.csv`)**
```csv
match_url,team,tackles_won,tackles,tackles_won_pct,blocks,interceptions,clearances,aerial_duels_won,aerial_duels
```

#### **5. Player Stats (`*_player_stats.csv`)**
```csv
match_url,player_name,team,table_source,position,minutes,goals,assists,shots_total,shots_on_target,passes_completed,passes_pct
```

#### **6. Match Events (`*_match_events.csv`)**
```csv
match_url,table_source,event_type,minute,player,team,description
```

---

## **⚙️ CONFIGURATION**

Edit `config.py` to customize settings:

```python
class Config:
    HEADLESS = True              # Browser mode (False for debugging)
    RATE_LIMIT_DELAY = 2         # Seconds between requests
    PAGE_TIMEOUT = 30000         # Page load timeout (ms)
    EXTRACT_PLAYER_STATS = True  # Include player data
    EXTRACT_MATCH_EVENTS = True  # Include match events
```

---

## **🔧 INTEGRATION WITH YOUR APP**

### **Method 1: Command Line Integration**
```python
import subprocess

# Your existing CSV generation
generate_season_urls('2024-25')  # Your function

# Run batch scraper
result = subprocess.run([
    'python', 'fbref_batch_scraper.py',
    '--input', 'season_2024_25.csv',
    '--output', 'results/',
    '--season', '2024-25'
], capture_output=True, text=True)

print(f"Scraping completed with status: {result.returncode}")
```

### **Method 2: Direct Python Integration**
```python
import asyncio
from fbref_batch_scraper import FBrefBatchScraper
from csv_handler import CSVHandler
from config import Config

async def scrape_season_data(csv_file: str, output_dir: str, season: str):
    config = Config()
    scraper = FBrefBatchScraper(config)
    csv_handler = CSVHandler()
    
    try:
        # Setup browser
        await scraper.setup_browser()
        
        # Read URLs
        urls = csv_handler.read_urls_from_csv(csv_file)
        
        # Scrape matches
        results = await scraper.scrape_match_batch(urls, season)
        
        # Save results
        csv_handler.save_results_to_csv(results, Path(output_dir), season)
        
        return len([r for r in results if 'error' not in r])
        
    finally:
        await scraper.cleanup()

# Usage
successful_matches = asyncio.run(scrape_season_data(
    'season_urls.csv', 
    'results/', 
    '2024-25'
))
```

---

## **📈 MONITORING & DEBUGGING**

### **Progress Monitoring:**
- Watch `batch_scraper.log` for real-time progress
- Check `*_scraping_summary.csv` for completion status
- Review `*_errors.csv` for failed extractions

### **Debugging Failed Extractions:**
1. Set `HEADLESS = False` in `config.py`
2. Set `SAVE_SCREENSHOTS = True` in `config.py`
3. Check individual match URLs manually in browser
4. Review error messages in logs

### **Performance Optimization:**
- Adjust `RATE_LIMIT_DELAY` based on FBref response
- Increase `PAGE_TIMEOUT` for slow connections
- Process smaller batches for testing

---

## **🎯 SAMPLE OUTPUT DATA**

### **Team Summary Example:**
```csv
match_url,team,possession,shots_total,shots_on_target,expected_goals,fouls,cards_yellow
https://fbref.com/.../Arsenal-Chelsea...,Arsenal,64.2,15,8,1.8,12,2
https://fbref.com/.../Arsenal-Chelsea...,Chelsea,35.8,8,3,0.6,15,1
```

### **Player Stats Example:**
```csv
match_url,player_name,team,position,minutes,goals,assists,shots_total,passes_completed
https://fbref.com/.../Arsenal-Chelsea...,Bukayo Saka,home,RW,90,1,0,4,45
https://fbref.com/.../Arsenal-Chelsea...,Reece James,away,RB,90,0,1,1,52
```

---

## **🚨 IMPORTANT NOTES**

### **Rate Limiting:**
- Default 2-second delay between requests
- Respects FBref's server capacity
- Adjust in `config.py` if needed

### **Anti-Scraping Measures:**
- System handles HTML comments automatically
- Multiple extraction fallback methods
- User-Agent rotation included

### **Data Quality:**
- Validates extracted data automatically
- Provides completeness scoring
- Maintains raw data for verification

### **Legal Compliance:**
- Respects robots.txt guidelines
- Implements reasonable rate limiting
- For educational/research use

---

## **🔍 TROUBLESHOOTING**

### **Common Issues:**

1. **No URLs Found in CSV**
   - Check column name matches `--url-column` parameter
   - Verify CSV format and encoding

2. **Browser Setup Failed**
   - Run `playwright install chromium`
   - Check system dependencies

3. **No Data Extracted**
   - Verify match URLs are accessible
   - Check FBref's current anti-scraping measures
   - Review logs for specific errors

4. **Rate Limiting Issues**
   - Increase `RATE_LIMIT_DELAY` in config
   - Process smaller batches
   - Check internet connection stability

---

## **📞 SUPPORT**

For issues or enhancements:
1. Check logs in `batch_scraper.log`
2. Review error CSV files
3. Test individual URLs manually
4. Adjust configuration settings

This comprehensive system gives you **complete control** over FBref data extraction and organizes it for immediate analysis!
