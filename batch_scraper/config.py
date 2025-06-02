"""
Configuration settings for the batch scraper
"""

class Config:
    """Configuration settings for the batch scraper"""
    
    # Browser settings
    HEADLESS = True  # Set to False for debugging
    
    # Rate limiting (seconds between requests)
    RATE_LIMIT_DELAY = 2
    
    # Timeouts (milliseconds)
    PAGE_TIMEOUT = 30000
    ELEMENT_TIMEOUT = 10000
    
    # Retry settings
    MAX_RETRIES = 3
    RETRY_DELAY = 5
    
    # Output settings
    SAVE_RAW_DATA = True
    SAVE_SCREENSHOTS = False  # Set to True for debugging
    
    # Data extraction settings
    EXTRACT_PLAYER_STATS = True
    EXTRACT_MATCH_EVENTS = True
    EXTRACT_DETAILED_STATS = True
