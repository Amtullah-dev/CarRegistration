# quick_test.py - Quick test without database
import os
import requests
from dotenv import load_dotenv

load_dotenv()

def quick_api_test():
    """Quick test to see if API parsing works"""
    url = "https://parseapi.back4app.com/classes/Car_Model_List"
    headers = {
        "X-Parse-Application-Id": os.getenv("PARSE_APP_ID"),
        "X-Parse-REST-API-Key": os.getenv("PARSE_API_KEY")
    }
    print(os.getenv("PARSE_APP_ID"))
    
    print("🔍 Testing API parsing...")
    
    total_fetched = 0
    valid_cars = 0
    skip = 0
    limit = 100
    
    # Test first few batches
    for batch_num in range(3):  # Test first 3 batches (300 records)
        try:
            params = {"limit": limit, "skip": skip}
            response = requests.get(url, headers=headers, params=params)
            data = response.json().get("results", [])
            
            if not data:
                print(f"No more data at batch {batch_num + 1}")
                break
            
            batch_valid = 0
            for car in data:
                make = car.get("Make", "").strip()
                model = car.get("Model", "").strip()
                year = car.get("Year")
                
                if make and model and year:
                    try:
                        int(year)  # Test if year is convertible
                        batch_valid += 1
                        valid_cars += 1
                    except:
                        pass
            
            total_fetched += len(data)
            skip += limit
            
            print(f"Batch {batch_num + 1}: {len(data)} records, {batch_valid} valid ({batch_valid/len(data)*100:.1f}%)")
            
            # Show sample data from first batch
            if batch_num == 0:
                print("Sample cars from first batch:")
                count = 0
                for car in data:
                    make = car.get("Make", "").strip()
                    model = car.get("Model", "").strip()
                    year = car.get("Year")
                    if make and model and year:
                        print(f"  - {make} {model} {year}")
                        count += 1
                        if count >= 5:  # Show first 5 valid cars
                            break
            
        except Exception as e:
            print(f"Error in batch {batch_num + 1}: {e}")
            break
    
    print(f"\n📊 Summary:")
    print(f"Total records fetched: {total_fetched}")
    print(f"Valid cars parsed: {valid_cars}")
    print(f"Success rate: {valid_cars/total_fetched*100:.1f}%")

if __name__ == "__main__":
    quick_api_test()