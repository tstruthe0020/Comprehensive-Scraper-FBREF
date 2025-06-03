#!/usr/bin/env python3
"""
FBref Batch Scraper - Main Script
Reads Match Report URLs from CSV and extracts comprehensive data
"""

import asyncio
import pandas as pd
import argparse
import os
from pathlib import Path
from typing import List, Dict, Any
import logging
from datetime import datetime
import json

from playwright.async_api import async_playwright
from data_processor import DataProcessor
from csv_handler import CSVHandler
from config import Config

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('batch_scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class FBrefBatchScraper:
    def __init__(self, config: Config):
        self.config = config
        self.browser = None
        self.page = None
        self.playwright = None
        self.data_processor = DataProcessor()
        self.csv_handler = CSVHandler()
        
    async def setup_browser(self):
        """Initialize browser with memory-optimized settings"""
        try:
            logger.info("Setting up browser...")
            self.playwright = await async_playwright().start()
            
            # Enhanced browser launch arguments to prevent memory issues
            self.browser = await self.playwright.chromium.launch(
                headless=self.config.HEADLESS,
                args=[
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-gpu',
                    '--disable-web-security',
                    '--disable-features=VizDisplayCompositor',
                    '--disable-extensions',
                    '--no-first-run',
                    '--disable-default-apps',
                    '--disable-background-timer-throttling',
                    '--disable-backgrounding-occluded-windows',
                    '--disable-renderer-backgrounding',
                    '--max-old-space-size=4096'  # Increase memory limit
                ]
            )
            
            # Create context with optimized settings
            self.context = await self.browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36'
            )
            
            self.page = await self.context.new_page()
            
            # Set longer timeouts to prevent premature cleanup
            self.page.set_default_timeout(60000)
            self.page.set_default_navigation_timeout(60000)
            
            logger.info("Browser setup completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Browser setup failed: {e}")
            return False
    
    async def extract_all_match_data(self, match_url: str, season: str) -> Dict[str, Any]:
        """Extract ALL available data from a match report page"""
        try:
            logger.info(f"Extracting data from: {match_url}")
            
            await self.page.goto(match_url, wait_until="domcontentloaded", timeout=30000)
            await self.page.wait_for_timeout(3000)
            
            # Initialize comprehensive data structure
            match_data = {
                'basic_info': {},
                'all_tables': {},
                'all_divs_with_data': {},
                'metadata': {
                    'match_url': match_url,
                    'season': season,
                    'extraction_timestamp': datetime.utcnow().isoformat(),
                    'page_title': await self.page.title(),
                    'total_tables_found': 0,
                    'total_data_points': 0
                }
            }
            
            # Extract basic match information
            match_data['basic_info'] = await self.extract_basic_match_info()
            
            # Extract ALL tables with complete structure
            match_data['all_tables'] = await self.extract_all_tables_comprehensive()
            
            # Extract any other elements that might contain data
            match_data['all_divs_with_data'] = await self.extract_data_elements()
            
            # Update metadata
            match_data['metadata']['total_tables_found'] = len(match_data['all_tables'])
            match_data['metadata']['total_data_points'] = self.count_total_data_points(match_data)
            
            logger.info(f"Successfully extracted {match_data['metadata']['total_tables_found']} tables with {match_data['metadata']['total_data_points']} data points")
            
            return match_data
            
        except Exception as e:
            logger.error(f"Error extracting data from {match_url}: {e}")
            return {}

    async def extract_all_tables_comprehensive(self) -> Dict[str, Any]:
        """Extract every single table on the page with complete metadata"""
        all_tables = {}
        
        try:
            tables = await self.page.query_selector_all("table")
            
            for i, table in enumerate(tables):
                table_key = f"table_{i}"
                
                table_data = {
                    'table_metadata': await self.extract_table_metadata(table, i),
                    'headers': await self.extract_table_headers(table),
                    'rows': await self.extract_table_rows(table),
                    'data_stat_mapping': await self.create_data_stat_mapping(table),
                    'table_text_content': await table.text_content()
                }
                
                all_tables[table_key] = table_data
                
        except Exception as e:
            logger.error(f"Error extracting tables: {e}")
        
        return all_tables

    async def extract_table_metadata(self, table, index: int) -> Dict[str, Any]:
        """Extract metadata about a table"""
        metadata = {
            'index': index,
            'id': await table.get_attribute("id") or f"no_id_{index}",
            'class': await table.get_attribute("class") or "",
            'data_attributes': {}
        }
        
        # Get all attributes
        try:
            all_attrs = await table.evaluate("element => Array.from(element.attributes).map(attr => ({name: attr.name, value: attr.value}))")
            metadata['all_attributes'] = all_attrs
        except:
            metadata['all_attributes'] = []
        
        return metadata

    async def extract_table_headers(self, table) -> List[Dict[str, Any]]:
        """Extract header information"""
        headers = []
        
        try:
            header_selectors = ["thead tr th", "thead tr td", "tbody tr:first-child th"]
            
            for selector in header_selectors:
                header_elements = await table.query_selector_all(selector)
                if header_elements:
                    for i, header in enumerate(header_elements):
                        header_data = {
                            'index': i,
                            'text': (await header.text_content()).strip(),
                            'data_stat': await header.get_attribute("data-stat") or "",
                            'title': await header.get_attribute("title") or ""
                        }
                        headers.append(header_data)
                    break
        except Exception as e:
            logger.warning(f"Error extracting headers: {e}")
        
        return headers

    async def extract_table_rows(self, table) -> List[Dict[str, Any]]:
        """Extract row data"""
        rows = []
        
        try:
            row_elements = await table.query_selector_all("tbody tr")
            
            for row_index, row in enumerate(row_elements):
                row_data = {
                    'row_index': row_index,
                    'cells': [],
                    'data_stat_values': {}
                }
                
                cells = await row.query_selector_all("td, th")
                
                for cell_index, cell in enumerate(cells):
                    cell_data = {
                        'cell_index': cell_index,
                        'text': (await cell.text_content()).strip(),
                        'data_stat': await cell.get_attribute("data-stat") or ""
                    }
                    
                    row_data['cells'].append(cell_data)
                    
                    if cell_data['data_stat']:
                        row_data['data_stat_values'][cell_data['data_stat']] = cell_data['text']
                
                rows.append(row_data)
                
        except Exception as e:
            logger.warning(f"Error extracting rows: {e}")
        
        return rows

    async def create_data_stat_mapping(self, table) -> Dict[str, str]:
        """Create mapping of data-stat attributes to values"""
        mapping = {}
        
        try:
            cells_with_data_stat = await table.query_selector_all("[data-stat]")
            
            for cell in cells_with_data_stat:
                data_stat = await cell.get_attribute("data-stat")
                text_value = (await cell.text_content()).strip()
                
                if data_stat and text_value:
                    if data_stat in mapping:
                        if isinstance(mapping[data_stat], list):
                            mapping[data_stat].append(text_value)
                        else:
                            mapping[data_stat] = [mapping[data_stat], text_value]
                    else:
                        mapping[data_stat] = text_value
                        
        except Exception as e:
            logger.warning(f"Error creating data-stat mapping: {e}")
        
        return mapping

    async def extract_basic_match_info(self) -> Dict[str, Any]:
        """Extract basic match information"""
        basic_info = {
            'page_title': await self.page.title(),
            'scorebox_data': {},
            'match_info_box': {}
        }
        
        try:
            # Scorebox information
            scorebox = await self.page.query_selector("div.scorebox")
            if scorebox:
                basic_info['scorebox_data'] = {
                    'text_content': await scorebox.text_content(),
                    'html': await scorebox.inner_html()
                }
            
            # Match info boxes
            info_selectors = ["div.info", "div#info", "div.meta", "div#meta"]
            for i, selector in enumerate(info_selectors):
                info_boxes = await self.page.query_selector_all(selector)
                for j, info_box in enumerate(info_boxes):
                    basic_info['match_info_box'][f'{selector}_{j}'] = {
                        'text': await info_box.text_content(),
                        'html': await info_box.inner_html()
                    }
                    
        except Exception as e:
            logger.warning(f"Error extracting basic info: {e}")
        
        return basic_info

    async def extract_data_elements(self) -> Dict[str, Any]:
        """Extract other data elements"""
        data_elements = {}
        
        try:
            # Look for elements with data-stat attributes outside tables
            all_data_stat_elements = await self.page.query_selector_all("[data-stat]:not(table *)")
            
            for i, element in enumerate(all_data_stat_elements):
                element_info = {
                    'tag': await element.evaluate("element => element.tagName"),
                    'data_stat': await element.get_attribute("data-stat"),
                    'text': await element.text_content()
                }
                data_elements[f'data_stat_{i}'] = element_info
                
        except Exception as e:
            logger.warning(f"Error extracting data elements: {e}")
        
        return data_elements

    def count_total_data_points(self, match_data: Dict[str, Any]) -> int:
        """Count total data points extracted"""
        total = 0
        
        try:
            for table_data in match_data.get('all_tables', {}).values():
                total += len(table_data.get('data_stat_mapping', {}))
        except:
            pass
        
        return total

    async def scrape_match_batch(self, urls: List[str], season: str = "2024-25") -> List[Dict[str, Any]]:
        """Scrape multiple matches with rate limiting"""
        results = []
        
        for i, url in enumerate(urls):
            try:
                logger.info(f"Processing match {i+1}/{len(urls)}: {url}")
                
                # Extract comprehensive data
                match_data = await self.extract_all_match_data(url, season)
                
                if match_data:
                    # Process the data into structured format
                    processed_data = self.data_processor.process_comprehensive_data(match_data)
                    results.append(processed_data)
                else:
                    logger.warning(f"No data extracted for: {url}")
                    results.append({'error': f'No data extracted from {url}'})
                
                # Rate limiting
                if i < len(urls) - 1:  # Don't sleep after last URL
                    await asyncio.sleep(self.config.RATE_LIMIT_DELAY)
                    
            except Exception as e:
                logger.error(f"Error processing {url}: {e}")
                results.append({'error': f'Error processing {url}: {str(e)}'})
        
        return results

    async def cleanup(self):
        """Clean up browser resources"""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

async def main():
    parser = argparse.ArgumentParser(description='FBref Batch Scraper')
    parser.add_argument('--input', required=True, help='Input CSV file with match URLs')
    parser.add_argument('--output', required=True, help='Output directory for results')
    parser.add_argument('--season', default='2024-25', help='Season identifier')
    parser.add_argument('--url-column', default='match_url', help='Column name containing URLs')
    
    args = parser.parse_args()
    
    # Load configuration
    config = Config()
    
    # Create output directory
    output_dir = Path(args.output)
    output_dir.mkdir(exist_ok=True)
    
    # Initialize scraper
    scraper = FBrefBatchScraper(config)
    csv_handler = CSVHandler()
    
    try:
        # Setup browser
        if not await scraper.setup_browser():
            logger.error("Failed to setup browser")
            return
        
        # Read input CSV
        logger.info(f"Reading URLs from: {args.input}")
        urls = csv_handler.read_urls_from_csv(args.input, args.url_column)
        
        if not urls:
            logger.error("No URLs found in input file")
            return
        
        logger.info(f"Found {len(urls)} URLs to process")
        
        # Scrape all matches
        results = await scraper.scrape_match_batch(urls, args.season)
        
        # Save results to multiple CSV files
        csv_handler.save_results_to_csv(results, output_dir, args.season)
        
        logger.info(f"Batch scraping completed. Results saved to: {output_dir}")
        
    except Exception as e:
        logger.error(f"Batch scraping failed: {e}")
    
    finally:
        await scraper.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
