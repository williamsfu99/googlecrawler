import json
from googlesearch import search
import time
import random
from web_scraper import WebScraper  # Assuming the WebScraper class is in web_scraper.py


def crawl_search_results(query, num_results=3):
    results = []
    
    for url in search(query):
        print(f"Crawling: {url}")
        scraper = WebScraper(url)
        scraper.scrape()
        results.append(scraper.data)

        if len(results) >= num_results:
            break

        # Add a random delay between requests
        time.sleep(random.uniform(1, 3))
    
    return results

def main():
    query = "ai resume generator"
    results = crawl_search_results(query)
    
    if results:
        output_file = 'search_results_analysis.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        print(f"Analysis complete. Results saved to {output_file}")
    else:
        print("No results were obtained. Check the console for error messages.")

if __name__ == "__main__":
    main()