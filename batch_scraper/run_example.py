#!/usr/bin/env python3
"""
Example script showing how to use the FBref Batch Scraper
"""

import asyncio
import pandas as pd
from pathlib import Path
from fbref_batch_scraper import FBrefBatchScraper
from csv_handler import CSVHandler
from config import Config
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def run_example_scraping():
    """Example of how to use the batch scraper"""
    
    # Configuration
    config = Config()
    config.HEADLESS = True  # Set to False for debugging
    config.RATE_LIMIT_DELAY = 3  # Be conservative with rate limiting
    
    # Initialize components
    scraper = FBrefBatchScraper(config)
    csv_handler = CSVHandler()
    
    # Create output directory
    output_dir = Path("example_results")
    output_dir.mkdir(exist_ok=True)
    
    try:
        logger.info("Starting example FBref batch scraping...")
        
        # Read URLs from example CSV
        urls = csv_handler.read_urls_from_csv("example_input.csv", "match_url")
        
        if not urls:
            logger.error("No URLs found in example_input.csv")
            return
        
        logger.info(f"Found {len(urls)} URLs to process")
        
        # Setup browser
        if not await scraper.setup_browser():
            logger.error("Failed to setup browser")
            return
        
        # Scrape matches (limit to first 2 for example)
        test_urls = urls[:2]  # Only scrape first 2 matches for demo
        logger.info(f"Processing {len(test_urls)} matches for demonstration")
        
        results = await scraper.scrape_match_batch(test_urls, "2024-25")
        
        # Save results
        csv_handler.save_results_to_csv(results, output_dir, "2024-25")
        
        # Print summary
        successful = len([r for r in results if 'error' not in r])
        failed = len([r for r in results if 'error' in r])
        
        logger.info(f"Scraping completed!")
        logger.info(f"Successful: {successful}, Failed: {failed}")
        logger.info(f"Results saved to: {output_dir}")
        
        # Show what files were created
        created_files = list(output_dir.glob("*.csv")) + list(output_dir.glob("*.json"))
        logger.info(f"Created {len(created_files)} output files:")
        for file in created_files:
            logger.info(f"  - {file.name}")
            
    except Exception as e:
        logger.error(f"Example scraping failed: {e}")
        
    finally:
        await scraper.cleanup()

def create_sample_csv():
    """Create a sample CSV file for testing"""
    
    sample_data = {
        'match_url': [
            'https://fbref.com/en/matches/d14fd5fb/Arsenal-Tottenham-September-15-2024-Premier-League',
            'https://fbref.com/en/matches/a7f2d9e1/Liverpool-Chelsea-January-26-2025-Premier-League',
            'https://fbref.com/en/matches/c4b8e7a2/Manchester-City-Arsenal-February-9-2025-Premier-League'
        ],
        'date': ['2024-09-15', '2025-01-26', '2025-02-09'],
        'home_team': ['Arsenal', 'Liverpool', 'Manchester City'],
        'away_team': ['Tottenham', 'Chelsea', 'Arsenal'],
        'season': ['2024-25', '2024-25', '2024-25']
    }
    
    df = pd.DataFrame(sample_data)
    df.to_csv('sample_matches.csv', index=False)
    print("Created sample_matches.csv for testing")

if __name__ == "__main__":
    print("FBref Batch Scraper - Example Usage")
    print("=" * 50)
    
    # Option 1: Create sample CSV
    print("1. Create sample CSV file")
    print("2. Run example scraping")
    
    choice = input("Enter choice (1 or 2): ").strip()
    
    if choice == "1":
        create_sample_csv()
    elif choice == "2":
        asyncio.run(run_example_scraping())
    else:
        print("Invalid choice. Please run again and select 1 or 2.")
