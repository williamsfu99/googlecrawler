import json
import csv
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException
import time
import re
import traceback

class WebScraper:
    def __init__(self, url, timeout=30, max_retries=3):
        self.url = url
        self.timeout = timeout
        self.max_retries = max_retries
        self.data = {
            "url": url,
            "title": "",
            "meta_tags": [],
            "main_content": [],
            "navigation_links": [],
            "links": [],
            "images": [],
            "videos": [],
            "structured_data": [],
            "open_graph": []
        }

    def clean_text(self, text):
        return re.sub(r'\s+', ' ', text).strip()

    def retry_on_stale(self, func):
        for attempt in range(self.max_retries):
            try:
                return func()
            except StaleElementReferenceException:
                if attempt == self.max_retries - 1:
                    raise
                time.sleep(1)

    def safe_find_elements(self, driver, by, value):
        return self.retry_on_stale(lambda: driver.find_elements(by, value))

    def safe_get_attribute(self, element, attribute):
        return self.retry_on_stale(lambda: element.get_attribute(attribute))

    def scrape(self):
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
        
        driver = webdriver.Chrome(options=chrome_options)
        
        try:
            driver.get(self.url)
            time.sleep(5)  # Wait for the page to load
            
            WebDriverWait(driver, self.timeout).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            self.scroll_page(driver)
            
            self.data["title"] = driver.title
            self.extract_meta_tags(driver)
            self.extract_main_content(driver)
            self.extract_navigation_links(driver)
            self.extract_links(driver)
            self.extract_images(driver)
            self.extract_videos(driver)
            self.extract_structured_data(driver)
            self.extract_open_graph(driver)
            
        except TimeoutException:
            print("Timed out waiting for page to load")
        except Exception as e:
            print(f"An error occurred: {e}")
            print(traceback.format_exc())
        finally:
            driver.quit()

    def scroll_page(self, driver):
        last_height = driver.execute_script("return document.body.scrollHeight")
        while True:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height

    def extract_meta_tags(self, driver):
        meta_tags = self.safe_find_elements(driver, By.TAG_NAME, "meta")
        self.data["meta_tags"] = [{"name": self.safe_get_attribute(tag, "name"), 
                                   "content": self.safe_get_attribute(tag, "content")} 
                                  for tag in meta_tags]

    def extract_main_content(self, driver):
        content_elements = self.safe_find_elements(driver, By.CSS_SELECTOR, "h1, h2, h3, h4, h5, h6, p, li")
        seen_content = set()
        for element in content_elements:
            text = self.clean_text(element.text)
            if text and len(text) > 5 and text not in seen_content:  # Ignore very short texts and duplicates
                self.data["main_content"].append(text)
                seen_content.add(text)

    def extract_navigation_links(self, driver):
        nav_elements = self.safe_find_elements(driver, By.CSS_SELECTOR, "nav a, header a, footer a")
        self.data["navigation_links"] = [self.safe_get_attribute(link, "href") for link in nav_elements if self.safe_get_attribute(link, "href")]

    def extract_links(self, driver):
        links = self.safe_find_elements(driver, By.TAG_NAME, "a")
        self.data["links"] = list(set(self.safe_get_attribute(link, 'href') for link in links if self.safe_get_attribute(link, 'href')))

    def extract_images(self, driver):
        images = self.safe_find_elements(driver, By.TAG_NAME, "img")
        self.data["images"] = [{"src": self.safe_get_attribute(img, 'src'), 
                                "alt": self.safe_get_attribute(img, 'alt')} 
                               for img in images if self.safe_get_attribute(img, 'src')]

    def extract_videos(self, driver):
        videos = self.safe_find_elements(driver, By.TAG_NAME, "video")
        self.data["videos"] = [self.safe_get_attribute(video, 'src') for video in videos if self.safe_get_attribute(video, 'src')]

    def extract_structured_data(self, driver):
        script_tags = self.safe_find_elements(driver, By.CSS_SELECTOR, "script[type='application/ld+json']")
        self.data["structured_data"] = [json.loads(tag.get_attribute('innerHTML')) for tag in script_tags]

    def extract_open_graph(self, driver):
        og_tags = self.safe_find_elements(driver, By.CSS_SELECTOR, "meta[property^='og:']")
        self.data["open_graph"] = [{"property": self.safe_get_attribute(tag, "property"), 
                                    "content": self.safe_get_attribute(tag, "content")} 
                                   for tag in og_tags]

    def save_as_json(self, filename="output.json"):
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=4)

    def save_as_csv(self, filename="output.csv"):
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["Section", "Content"])
            for key, value in self.data.items():
                if isinstance(value, list):
                    for item in value:
                        writer.writerow([key, json.dumps(item) if isinstance(item, dict) else item])
                else:
                    writer.writerow([key, value])

# The rest of the script (scrape_website function and main block) remains the same

def scrape_website(url, output_format='json', output_file=None):
    scraper = WebScraper(url)
    scraper.scrape()
    
    if output_format == 'json':
        output_file = output_file or "output.json"
        scraper.save_as_json(output_file)
    elif output_format == 'csv':
        output_file = output_file or "output.csv"
        scraper.save_as_csv(output_file)
    else:
        print("Invalid output format. Please choose 'json' or 'csv'.")
    
    print(f"Scraping completed. Output saved to {output_file}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Web Scraper")
    parser.add_argument("url", help="URL of the website to scrape")
    parser.add_argument("--format", choices=['json', 'csv'], default='json', help="Output format (default: json)")
    parser.add_argument("--output", help="Output file name")
    args = parser.parse_args()

    scrape_website(args.url, args.format, args.output)