import requests
from bs4 import BeautifulSoup
from googlesearch import search
import json
from urllib.parse import urljoin
import time
import random

def get_page_content(url):
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Referer': 'https://www.google.com/'
        }
        response = requests.get(url, timeout=15, headers=headers)
        response.raise_for_status()
        return response.text
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 403:
            print(f"403 Forbidden error for {url}. The website may be blocking scrapers.")
        else:
            print(f"HTTP error occurred for {url}: {e}")
    except requests.exceptions.ReadTimeout:
        print(f"Read timeout occurred for {url}. The server took too long to respond.")
    except requests.RequestException as e:
        print(f"Error fetching {url}: {e}")
    return None

def extract_page_info(html, base_url):
    if html is None:
        return None
    
    soup = BeautifulSoup(html, 'html.parser')
    
    # Extract meta tags
    meta_tags = {}
    for meta in soup.find_all('meta'):
        name = meta.get('name') or meta.get('property')
        if name:
            meta_tags[name] = meta.get('content')

    # Extract title
    title = soup.title.string if soup.title else None

    # Extract text content with structure
    content = []
    for element in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p']):
        if element.name.startswith('h'):
            content.append({
                'type': 'heading',
                'level': int(element.name[1]),
                'text': element.get_text(strip=True)
            })
        else:
            content.append({
                'type': 'paragraph',
                'text': element.get_text(strip=True)
            })
    
    # Extract navigation links
    nav_links = []
    nav_elements = soup.find_all('nav')
    if not nav_elements:
        nav_elements = soup.find_all(class_=lambda x: x and 'nav' in x.lower())
    
    for nav in nav_elements:
        for a in nav.find_all('a', href=True):
            nav_links.append({
                'text': a.get_text(strip=True),
                'url': urljoin(base_url, a['href']),
                'title': a.get('title')
            })
    
    # Extract all links
    links = []
    for a in soup.find_all('a', href=True):
        links.append({
            'text': a.get_text(strip=True),
            'url': urljoin(base_url, a['href']),
            'title': a.get('title'),
            'rel': a.get('rel')
        })
    
    # Extract images
    images = []
    for img in soup.find_all('img'):
        images.append({
            'url': urljoin(base_url, img.get('src', '')),
            'alt': img.get('alt', ''),
            'title': img.get('title'),
            'width': img.get('width'),
            'height': img.get('height')
        })
    
    # Extract videos
    videos = []
    for video in soup.find_all('video'):
        videos.append({
            'url': urljoin(base_url, video.get('src', '')),
            'width': video.get('width'),
            'height': video.get('height'),
            'poster': urljoin(base_url, video.get('poster', ''))
        })
    
    # Extract schema.org structured data
    structured_data = []
    for script in soup.find_all('script', type='application/ld+json'):
        try:
            if script.string:
                structured_data.append(json.loads(script.string))
        except json.JSONDecodeError:
            print(f"Error parsing JSON-LD in {base_url}")
    
    # Extract Open Graph tags
    og_tags = {}
    for meta in soup.find_all('meta', property=lambda x: x and x.startswith('og:')):
        og_tags[meta['property'][3:]] = meta['content']
    
    return {
        "url": base_url,
        "title": title,
        "meta_tags": meta_tags,
        "content": content,
        "navigation_links": nav_links,
        "links": links,
        "images": images,
        "videos": videos,
        "structured_data": structured_data,
        "open_graph": og_tags
    }

def crawl_search_results(query, num_results=10):
    results = []
    
    for url in search(query):
        print(f"Crawling: {url}")
        html_content = get_page_content(url)
        
        if html_content:
            page_info = extract_page_info(html_content, url)
            if page_info:
                results.append(page_info)
        
        if len(results) >= num_results:
            break
        
        # Add a random delay between requests
        time.sleep(random.uniform(1, 3))
    
    return results

def main():
    query = "AI image generator"
    results = crawl_search_results(query)
    
    if results:
        with open('search_results_analysis.json', 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        print(f"Analysis complete. Results saved to search_results_analysis.json")
    else:
        print("No results were obtained. Check the console for error messages.")

if __name__ == "__main__":
    main()