import time
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from newspaper import Article

# List of Baeldung article URLs to scrape
java_sources = [
    "https://www.baeldung.com/java-collections",
    "https://www.baeldung.com/java-streams",
    "https://www.baeldung.com/java-concurrency",
    "https://www.baeldung.com/java-tutorial",
    "https://www.baeldung.com/get-started-with-java-series"
]

# Step 1: Use Selenium to fetch full HTML
def get_html_with_selenium(url, wait_time=5):
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--window-size=1280,800")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64)")
    
    driver = webdriver.Chrome(options=options)
    driver.get(url)
    time.sleep(wait_time)
    html = driver.page_source
    driver.quit()
    return html

# Step 2: Use newspaper3k to extract title and text
def extract_article_from_html(url, html):
    if not html:
        raise ValueError("No HTML to parse")
    article = Article(url)
    article.download(input_html=html)
    article.parse()
    return article.title, article.text

# Step 3: Save article to disk
def save_article(title, content, folder="baeldung_articles"):
    os.makedirs(folder, exist_ok=True)
    safe_title = "".join(c if c.isalnum() or c in " -_" else "_" for c in title)
    filepath = os.path.join(folder, f"{safe_title}.txt")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"📁 Saved: {filepath}")

# Step 4: Loop through URLs and extract content
def scrape_baeldung_articles(urls):
    results = []
    for url in urls:
        try:
            html = get_html_with_selenium(url)
            title, content = extract_article_from_html(url, html)
            save_article(title, content)
            results.append({"url": url, "title": title, "content": content})
            print(f"✅ Scraped: {title}")
        except Exception as e:
            print(f"❌ Failed to scrape {url}: {e}")
    return results

# Step 5: Run the scraper
if __name__ == "__main__":
    articles = scrape_baeldung_articles(java_sources)
    for article in articles:
        print("\n---")
        print(f"Title: {article['title']}")
        print(f"URL: {article['url']}")
        print(f"Preview:\n{article['content'][:500]}")
