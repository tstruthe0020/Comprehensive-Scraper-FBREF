
import requests
import sys
import json

class FBREFScraperTester:
    def __init__(self, base_url="https://90280e76-97e5-45e5-996a-34bbf3ba566e.preview.emergentagent.com"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0

    def run_test(self, name, method, endpoint, expected_status, data=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                return success, response.json() if response.content else {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                return success, response.json() if response.content else {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_health_endpoint(self):
        """Test the health endpoint"""
        success, response = self.run_test(
            "Health Endpoint",
            "GET",
            "api/health",
            200
        )
        if success:
            print(f"Health endpoint response: {response}")
        return success

    def test_scrape_valid_url(self, url):
        """Test scraping with a valid FBREF URL"""
        success, response = self.run_test(
            "Scrape Valid URL",
            "POST",
            "api/scrape-fbref",
            200,
            data={"url": url}
        )
        if success:
            print(f"Success: {response['success']}")
            print(f"Message: {response['message']}")
            print(f"Links found: {len(response['links'])}")
            print(f"First few links: {response['links'][:3] if response['links'] else []}")
            print(f"CSV data available: {'Yes' if response['csv_data'] else 'No'}")
        return success, response

    def test_scrape_invalid_url(self, url):
        """Test scraping with an invalid URL"""
        success, response = self.run_test(
            "Scrape Invalid URL",
            "POST",
            "api/scrape-fbref",
            200,  # The API returns 200 even for errors, with success: false
            data={"url": url}
        )
        if success:
            print(f"Success: {response['success']}")
            print(f"Error message: {response['message']}")
        return success, response
        
    def test_demo_scrape(self):
        """Test the demo scrape endpoint"""
        success, response = self.run_test(
            "Demo Scrape",
            "POST",
            "api/demo-scrape",
            200
        )
        if success:
            print(f"Success: {response['success']}")
            print(f"Message: {response['message']}")
            print(f"Links found: {len(response['links'])}")
            print(f"First few links: {response['links'][:3] if response['links'] else []}")
            print(f"CSV data available: {'Yes' if response['csv_data'] else 'No'}")
            
            # Verify we have exactly 5 demo links as expected
            if len(response['links']) == 5:
                print("✅ Demo returned exactly 5 links as expected")
            else:
                print(f"❌ Demo returned {len(response['links'])} links instead of 5")
                
            # Verify CSV format contains expected headers
            if "Match_Report_URL,Home_Team,Away_Team,Date,Score" in response['csv_data']:
                print("✅ CSV contains match data headers")
            else:
                print("❌ CSV missing match data headers")
                
            if "=== PLAYER DATA ===" in response['csv_data']:
                print("✅ CSV contains player data section")
            else:
                print("❌ CSV missing player data section")
        return success, response

def main():
    # Setup
    tester = FBREFScraperTester()
    
    # Test health endpoint
    health_success = tester.test_health_endpoint()
    if not health_success:
        print("❌ Health endpoint failed, stopping tests")
        return 1
        
    # Test demo scrape endpoint
    demo_success, demo_response = tester.test_demo_scrape()
    if not demo_success:
        print("❌ Demo scrape endpoint failed")
    
    # Test valid URL
    valid_url = "https://fbref.com/en/comps/9/schedule/Premier-League-Scores-and-Fixtures"
    valid_success, valid_response = tester.test_scrape_valid_url(valid_url)
    
    # Test invalid URL (not FBREF)
    invalid_url = "https://example.com"
    invalid_success, invalid_response = tester.test_scrape_invalid_url(invalid_url)
    
    # Test malformed URL
    malformed_url = "not-a-url"
    malformed_success, malformed_response = tester.test_scrape_invalid_url(malformed_url)
    
    # Print results
    print(f"\n📊 Tests passed: {tester.tests_passed}/{tester.tests_run}")
    
    # Check if the demo test returned links and CSV data
    if demo_success and demo_response['success']:
        has_links = len(demo_response['links']) == 5
        has_csv = bool(demo_response['csv_data'])
        
        print(f"\nDemo test results:")
        print(f"- Found 5 links: {'✅' if has_links else '❌'}")
        print(f"- Generated CSV: {'✅' if has_csv else '❌'}")
    
    # Check if the valid URL test returned links and CSV data
    if valid_success and valid_response['success']:
        has_links = len(valid_response['links']) > 0
        has_csv = bool(valid_response['csv_data'])
        
        print(f"\nValid URL test results:")
        print(f"- Found links: {'✅' if has_links else '❌'}")
        print(f"- Generated CSV: {'✅' if has_csv else '❌'}")
        
        # Check if links match expected pattern
        if has_links:
            pattern_match = all('/matches/' in link for link in valid_response['links'])
            print(f"- Links match expected pattern: {'✅' if pattern_match else '❌'}")
    
    # Check if error handling works correctly
    if invalid_success:
        print(f"\nInvalid URL test results:")
        print(f"- API returned error: {'✅' if not invalid_response['success'] else '❌'}")
    
    if malformed_success:
        print(f"\nMalformed URL test results:")
        print(f"- API returned error: {'✅' if not malformed_response['success'] else '❌'}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
