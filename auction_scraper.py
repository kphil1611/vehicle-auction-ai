import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import datetime
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

# Function to scrape vehicle data from auction site (example: SYNETIQ)
def scrape_auction_data():
    print("🔄 Starting auction data scraping...")

    # Set up Selenium Chrome WebDriver
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run in headless mode for GitHub Actions
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    # Initialize WebDriver
    service = Service("/usr/bin/chromedriver")  # Adjust path if needed
    driver = webdriver.Chrome(service=service, options=chrome_options)

    try:
        # Open the SYNETIQ auction page
        print("🌐 Navigating to SYNETIQ auction site...")
        driver.get("https://auctions.synetiq.co.uk/")

        time.sleep(3)  # Wait for elements to load

        # Try to find and click the "Accept Recommended" button
        try:
            accept_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Accept Recommended')]")
            accept_button.click()
            print("✅ Cookie popup dismissed.")
        except Exception as e:
            print(f"⚠️ No cookie popup detected or already accepted: {e}")

        time.sleep(2)  # Allow time for the page to update

        # Now proceed to scrape the auctions
        print("🔍 Searching for vehicle listings...")
        auctions = driver.find_elements(By.CLASS_NAME, "vehicle-card")  # Update with actual class name
        vehicles = []
        print(f"✅ Found {len(auctions)} vehicles.")

        for auction in auctions:
            try:
                title = auction.find_element(By.CLASS_NAME, "vehicle-title").text.strip()
                price = auction.find_element(By.CLASS_NAME, "current-bid").text.strip()
                year = int(title.split()[0])  # Extract year from title
                category = auction.find_element(By.CLASS_NAME, "damage-category").text.strip()
                mileage = int(auction.find_element(By.CLASS_NAME, "mileage").text.replace(" miles", "").replace(",", ""))

                # Store data
                vehicles.append({
                    "Title": title,
                    "Price": int(price.replace("£", "").replace(",", "")),
                    "Year": year,
                    "Category": category,
                    "Mileage": mileage
                })
            except Exception as e:
                print(f"⚠️ Skipping a vehicle due to error: {e}")
                continue

        print(f"✅ Successfully scraped {len(vehicles)} vehicles.")
        return vehicles

    finally:
        driver.quit()  # Close the browser when done

# Function to estimate repair costs based on damage type
def estimate_repair_cost(category):
    repair_costs = {
        "CAT N": 2500,  # Non-structural damage estimate
        "CAT S": 4000,  # Structural damage estimate
        "CAT D": 3000,  # Older damage classification
        "CAT C": 4500
    }
    return repair_costs.get(category, 2000)  # Default cost if unknown

# Function to estimate resale price (placeholder, can integrate eBay/AutoTrader scraping later)
def estimate_resale_price(title):
    base_prices = {  # Placeholder values based on make/model (can be improved)
        "Ford Ranger": 14000,
        "Vauxhall Grandland": 11000,
        "BMW X3": 15000
    }
    for key in base_prices:
        if key in title:
            return base_prices[key]
    return 8000  # Default resale price if unknown

# Function to calculate maximum bid
def calculate_max_bid(vehicle):
    repair_cost = estimate_repair_cost(vehicle["Category"])
    resale_price = estimate_resale_price(vehicle["Title"])
    auction_fees = 350  # Estimated auction fees
    transport_costs = 200  # Estimated transport costs
    desired_profit = 3000  # Minimum profit required
    
    max_bid = resale_price - (repair_cost + auction_fees + transport_costs + desired_profit)
    return max_bid

# Main execution
def main():
    print("🚀 Starting main execution...")

    vehicles = scrape_auction_data()

    if not vehicles:
        print("❌ No vehicles scraped. Exiting...")
        return
    
    results = []
    for vehicle in vehicles:
        max_bid = calculate_max_bid(vehicle)
        vehicle["Max Bid"] = max_bid
        results.append(vehicle)

    # Convert to DataFrame and save results
    df = pd.DataFrame(results)
    
    # Save with timestamp
    filename = f"auction_results_{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.csv"
    df.to_csv(filename, index=False)

    # Confirm file creation
    if os.path.exists(filename):
        print(f"✅ Results successfully saved to {filename}")
    else:
        print("❌ ERROR: CSV file was not created!")

    # Auto-commit file to GitHub
    print("📤 Preparing to commit results to GitHub...")

    os.system("git config --global user.email 'github-actions@github.com'")
    os.system("git config --global user.name 'GitHub Actions'")

    os.system(f'git add {filename}')
    os.system(f'git commit -m "Auto-generated auction results: {filename}"')
    os.system("git push origin main")

    print("✅ Results committed to GitHub!")

# Run script
if __name__ == "__main__":
    main()
